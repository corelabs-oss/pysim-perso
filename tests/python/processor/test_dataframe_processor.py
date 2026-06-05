# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
import pandas as pd
import pytest

from gsm_data_generator.processor.process import DataFrameProcessor
from gsm_data_generator.algorithm.encode import EncodingUtils
from gsm_data_generator.transform.transform import DataTransform

COLS = ["ICCID", "IMSI", "PIN1", "PUK1"]


# ------------------------------------------------------------------ #
# generate_empty_dataframe
# ------------------------------------------------------------------ #

def test_generate_empty_dataframe_shape():
    df = DataFrameProcessor.generate_empty_dataframe(COLS, "5")
    assert df.shape == (5, len(COLS))


def test_generate_empty_dataframe_column_names():
    cols = ["A", "B", "C"]
    df = DataFrameProcessor.generate_empty_dataframe(cols, "3")
    assert list(df.columns) == cols


def test_generate_empty_dataframe_all_zeros():
    df = DataFrameProcessor.generate_empty_dataframe(["X", "Y"], "4")
    assert (df == 0).all().all()


def test_generate_empty_dataframe_single_row():
    df = DataFrameProcessor.generate_empty_dataframe(["COL"], "1")
    assert len(df) == 1


# ------------------------------------------------------------------ #
# initialize_column
# ------------------------------------------------------------------ #

def test_initialize_column_incrementing():
    df = DataFrameProcessor.generate_empty_dataframe(["ICCID"], "4")
    DataFrameProcessor.initialize_column(df, "ICCID", "100")
    assert list(df["ICCID"]) == [100, 101, 102, 103]


def test_initialize_column_static():
    df = DataFrameProcessor.generate_empty_dataframe(["OP"], "3")
    DataFrameProcessor.initialize_column(df, "OP", "ABCD1234", increment=False)
    assert list(df["OP"]) == ["ABCD1234", "ABCD1234", "ABCD1234"]


def test_initialize_column_adds_new_column():
    df = DataFrameProcessor.generate_empty_dataframe(["A"], "2")
    DataFrameProcessor.initialize_column(df, "NEW", "10")
    assert "NEW" in df.columns
    assert list(df["NEW"]) == [10, 11]


def test_initialize_column_zero_start():
    df = DataFrameProcessor.generate_empty_dataframe(["N"], "3")
    DataFrameProcessor.initialize_column(df, "N", "0")
    assert list(df["N"]) == [0, 1, 2]


# ------------------------------------------------------------------ #
# apply_function_to_column
# ------------------------------------------------------------------ #

def test_apply_function_to_column_transforms_values():
    df = pd.DataFrame({"src": ["abc", "def"], "dest": ["", ""]})
    DataFrameProcessor.apply_function_to_column(df, "dest", "src", str.upper)
    assert list(df["dest"]) == ["ABC", "DEF"]


def test_apply_function_to_column_no_op_when_dest_missing():
    df = pd.DataFrame({"src": ["abc"]})
    DataFrameProcessor.apply_function_to_column(df, "nonexistent", "src", str.upper)
    assert "nonexistent" not in df.columns


def test_apply_function_to_column_lambda():
    df = pd.DataFrame({"ki": ["aabb"], "eki": ["0000"]})
    DataFrameProcessor.apply_function_to_column(df, "eki", "ki", lambda x: x[:2])
    assert df["eki"].iloc[0] == "aa"


# ------------------------------------------------------------------ #
# clip_columns
# ------------------------------------------------------------------ #

def test_clip_columns_single_column():
    df = pd.DataFrame({"A": ["ABCDEF"]})
    result = DataFrameProcessor.clip_columns(df, [0], [2])
    assert result["A"].iloc[0] == "ABC"


def test_clip_columns_multiple_columns():
    df = pd.DataFrame({"A": ["ABCDEF"], "B": ["123456"]})
    result = DataFrameProcessor.clip_columns(df, [0, 2], [2, 4])
    assert result["A"].iloc[0] == "ABC"
    assert result["B"].iloc[0] == "345"


def test_clip_columns_full_range():
    df = pd.DataFrame({"X": ["HELLO"]})
    result = DataFrameProcessor.clip_columns(df, [0], [4])
    assert result["X"].iloc[0] == "HELLO"


def test_clip_columns_single_char():
    df = pd.DataFrame({"X": ["HELLO"]})
    result = DataFrameProcessor.clip_columns(df, [1], [1])
    assert result["X"].iloc[0] == "E"


def test_clip_columns_multiple_rows():
    df = pd.DataFrame({"A": ["ABCDEF", "GHIJKL"]})
    result = DataFrameProcessor.clip_columns(df, [0], [2])
    assert result["A"].iloc[0] == "ABC"
    assert result["A"].iloc[1] == "GHI"


# ------------------------------------------------------------------ #
# add_duplicate_columns
# ------------------------------------------------------------------ #

def test_add_duplicate_columns_creates_numbered_copies():
    df = pd.DataFrame({"KI": ["AABBCC"]})
    headers = ["KI", "KI0", "KI1"]
    result = DataFrameProcessor.add_duplicate_columns(df, 2, headers)
    assert list(result.columns) == headers
    assert result["KI0"].iloc[0] == "AABBCC"
    assert result["KI1"].iloc[0] == "AABBCC"


def test_add_duplicate_columns_returns_only_listed_headers():
    df = pd.DataFrame({"A": ["X"], "B": ["Y"]})
    headers = ["A", "A0", "B"]
    result = DataFrameProcessor.add_duplicate_columns(df, 1, headers)
    assert list(result.columns) == headers


def test_add_duplicate_columns_values_match_source():
    df = pd.DataFrame({"ICCID": ["1234567890"]})
    headers = ["ICCID", "ICCID0", "ICCID1", "ICCID2"]
    result = DataFrameProcessor.add_duplicate_columns(df, 3, headers)
    for col in headers:
        assert result[col].iloc[0] == "1234567890"


# ------------------------------------------------------------------ #
# encode_dataframe / decode_dataframe
# ------------------------------------------------------------------ #

def test_encode_dataframe_applies_pin_encoding():
    df = pd.DataFrame({"PIN1": ["1234"]})
    result = DataFrameProcessor.encode_dataframe(df.copy())
    assert result["PIN1"].iloc[0] == EncodingUtils.enc_pin("1234")


def test_encode_dataframe_applies_puk_s2h():
    df = pd.DataFrame({"PUK1": ["12345678"]})
    result = DataFrameProcessor.encode_dataframe(df.copy())
    assert result["PUK1"].iloc[0] == DataTransform.s2h("12345678")


def test_encode_dataframe_applies_adm_s2h():
    df = pd.DataFrame({"ADM1": ["11111111"]})
    result = DataFrameProcessor.encode_dataframe(df.copy())
    assert result["ADM1"].iloc[0] == DataTransform.s2h("11111111")


def test_encode_dataframe_leaves_unknown_columns_unchanged():
    df = pd.DataFrame({"KI": ["AABBCCDD"], "UNKNOWN": ["untouched"]})
    result = DataFrameProcessor.encode_dataframe(df.copy())
    assert result["KI"].iloc[0] == "AABBCCDD"
    assert result["UNKNOWN"].iloc[0] == "untouched"


def test_encode_dataframe_skips_missing_columns():
    df = pd.DataFrame({"PIN1": ["1234"]})
    # No PIN2 column — should not raise
    result = DataFrameProcessor.encode_dataframe(df.copy())
    assert "PIN2" not in result.columns


@pytest.mark.parametrize("pin", ["1234", "0000", "9999"])
def test_encode_decode_pin_roundtrip(pin):
    df = pd.DataFrame({"PIN1": [pin], "PIN2": [pin]})
    encoded = DataFrameProcessor.encode_dataframe(df.copy())
    decoded = DataFrameProcessor.decode_dataframe(encoded.copy())
    assert decoded["PIN1"].iloc[0] == pin
    assert decoded["PIN2"].iloc[0] == pin


@pytest.mark.parametrize("imsi", ["111111111111111", "410092078615999"])
def test_encode_decode_imsi_roundtrip(imsi):
    df = pd.DataFrame({"IMSI": [imsi]})
    encoded = DataFrameProcessor.encode_dataframe(df.copy())
    assert encoded["IMSI"].iloc[0] != imsi  # confirm encoding changed the value
    decoded = DataFrameProcessor.decode_dataframe(encoded.copy())
    assert decoded["IMSI"].iloc[0] == imsi
