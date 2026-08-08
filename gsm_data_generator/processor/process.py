from typing import List, Dict, Any, Tuple
import pandas as pd
import collections
from ..transform import DataTransform
from ..algorithm import EncodingUtils


class DataProcessing:

    @staticmethod
    def split_range(input_string: str) -> Tuple[int, int]:
        if input_string and "-" in input_string and len(input_string) > 2:
            values = input_string.split("-")
            return int(values[0]), int(values[1])
        return 0, 32

    @staticmethod
    def extract_ranges(ranges: List[str]) -> Tuple[List[int], List[int]]:
        left_ranges, right_ranges = [], []
        for range_str in ranges:
            left, right = DataProcessing.split_range(range_str)
            left_ranges.append(left)
            right_ranges.append(right)
        return left_ranges, right_ranges

    @staticmethod
    def find_duplicates(items: List[Any]) -> List[Any]:
        return [item for item, count in collections.Counter(items).items() if count > 1]

    @staticmethod
    def ordered_entries(param_dict: Dict[str, List[str]]) -> List[List[str]]:
        """Return the entries of `param_dict` in laser-position order.

        Keys of ``laser_variables`` are laser print positions, so "10" must
        follow "9" rather than landing wherever JSON insertion order put it.
        Sorting numerically also avoids the lexicographic ordering that would
        otherwise place "10" between "1" and "2".

        Falls back to insertion order when the keys are not all numeric, so
        callers passing arbitrarily-keyed dictionaries are unaffected.
        """
        keys = list(param_dict.keys())
        if keys and all(isinstance(k, str) and k.isdigit() for k in keys):
            keys = sorted(keys, key=int)
        return [param_dict[k] for k in keys]

    @staticmethod
    def max_duplicate_suffix(headers: List[str], columns) -> int:
        """Highest numeric suffix needed to build `headers` out of `columns`.

        :meth:`append_count_to_duplicates` renames repeated selections to
        ``NAME``, ``NAME1``, ``NAME2`` ..., so the number of duplicate columns
        that has to be materialised depends on the configuration rather than
        on a fixed constant.
        """
        existing = set(columns)
        highest = 0
        for header in headers:
            if header in existing:
                continue
            # Try the longest base first: "KIC11" is "KIC1" + "1", not
            # "KIC" + "11", because KIC1 is itself a real column.
            for split in range(len(header) - 1, 0, -1):
                base, suffix = header[:split], header[split:]
                if suffix.isdigit() and base in existing:
                    highest = max(highest, int(suffix))
                    break
        return highest

    @staticmethod
    def extract_parameter_info(
        param_dict: Dict[str, List[str]],
    ) -> Tuple[List[str], List[str], set, List[str], List[int], List[int]]:
        values, classes, ranges = [], [], []
        for item in DataProcessing.ordered_entries(param_dict):
            values.append(item[0])
            classes.append(item[1])
            ranges.append(item[2])

        renamed_values = DataProcessing.append_count_to_duplicates(values)
        duplicate_values = DataProcessing.find_duplicates(values)
        unique_values = set(values)
        left_ranges, right_ranges = DataProcessing.extract_ranges(ranges)

        return (
            renamed_values,
            duplicate_values,
            unique_values,
            classes,
            left_ranges,
            right_ranges,
        )

    @staticmethod
    def append_count_to_duplicates(input_list: List[str]) -> List[str]:
        output_list = []
        element_counts: Dict[str, int] = {}

        for element in input_list:
            if element in element_counts:
                element_counts[element] += 1
                output_list.append(f"{element}{element_counts[element]}")
            else:
                element_counts[element] = 0
                output_list.append(element)

        return output_list


class DataFrameProcessor:
    @staticmethod
    def generate_empty_dataframe(columns: List[str], rows) -> pd.DataFrame:
        # Built directly rather than from a list of per-row dicts: the latter
        # materialised one dict per row (23 keys x N rows) before pandas ever
        # saw the data, which dominated memory at large sizes.
        return pd.DataFrame(0, index=pd.RangeIndex(int(rows)), columns=list(columns))

    @staticmethod
    def initialize_column(
        df: pd.DataFrame, column: str, start_value: str, increment: bool = True
    ) -> None:
        if increment:
            df[column] = range(int(start_value), int(start_value) + len(df))
        else:
            df[column] = str(start_value)

    @staticmethod
    def initialize_identifier_column(
        df: pd.DataFrame,
        column: str,
        start_value: str,
        prefix_length: int = 0,
    ) -> None:
        """Fill `column` with a fixed-width, zero-padded identifier sequence.

        Unlike :meth:`initialize_column`, the identifier is treated as a digit
        string rather than an integer, which matters in two ways:

        * Leading zeros survive. ``int()`` drops them, so a test-network IMSI
          of "001010000000001" became the 13-digit "1010000000001".
        * Only the digits after `prefix_length` are incremented, so a carry
          cannot propagate into a structural prefix. Incrementing an IMSI as a
          whole number lets the MSIN overflow into the MNC — "410099999999999"
          + 1 becomes "410100000000000", moving the batch to a different
          operator.

        Raises
        ------
        ValueError
            If `start_value` is not numeric, `prefix_length` is out of range,
            or the requested row count overflows the incrementable suffix.
        """
        start = str(start_value)
        if not start.isdigit():
            raise ValueError(
                f"{column} must be a numeric identifier string, got {start!r}"
            )
        if not 0 <= prefix_length < len(start):
            raise ValueError(
                f"{column} prefix_length must be within [0, {len(start)}), "
                f"got {prefix_length}"
            )

        prefix = start[:prefix_length]
        suffix = start[prefix_length:]
        width = len(suffix)
        first = int(suffix)
        last = first + len(df) - 1

        if last >= 10**width:
            raise ValueError(
                f"{column} sequence overflows its {width}-digit incrementable "
                f"field: starting at {start} for {len(df)} rows would carry "
                f"into the fixed prefix {prefix!r}. "
                f"Reduce size or lower the starting value."
            )

        df[column] = [f"{prefix}{n:0{width}d}" for n in range(first, last + 1)]

    @staticmethod
    def apply_function_to_column(
        df: pd.DataFrame, dest_col: str, src_col: str, func
    ) -> None:
        if dest_col in df.columns:
            df[dest_col] = df[src_col].apply(func)

    @staticmethod
    def clip_columns(
        df: pd.DataFrame, left_ranges: List[int], right_ranges: List[int]
    ) -> pd.DataFrame:
        for col, left, right in zip(df.columns, left_ranges, right_ranges):
            df[col] = df[col].apply(lambda x: x[left : right + 1])
        return df

    @staticmethod
    def add_duplicate_columns(
        df: pd.DataFrame, limit: int, headers: List[str]
    ) -> pd.DataFrame:
        for c in range(limit):
            for col in df.columns:
                new_col = f"{col}{c}"
                if new_col in headers:
                    df[new_col] = df[col]
        return df[headers]

    @staticmethod
    def encode_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        encoding_map = {
            "ICCID": EncodingUtils.enc_iccid,
            "IMSI": EncodingUtils.enc_imsi,
            "PIN1": EncodingUtils.enc_pin,
            "PUK1": DataTransform.s2h,
            "PIN2": EncodingUtils.enc_pin,
            "PUK2": DataTransform.s2h,
            "ADM1": DataTransform.s2h,
            "ADM6": DataTransform.s2h,
        }
        for col, func in encoding_map.items():
            if col in df.columns:
                df[col] = df[col].apply(func)
        return df

    @staticmethod
    def decode_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        decoding_map = {
            "ICCID": EncodingUtils.dec_iccid,
            "IMSI": EncodingUtils.dec_imsi,
            "PIN1": EncodingUtils.dec_pin,
            "PUK1": DataTransform.h2s,
            "PIN2": EncodingUtils.dec_pin,
            "PUK2": DataTransform.h2s,
            "ADM1": DataTransform.h2s,
        }
        for col, func in decoding_map.items():
            if col in df.columns:
                df[col] = df[col].apply(func)
        return df


__all__ = [
    "DataProcessing",
    "DataFrameProcessor",
]
