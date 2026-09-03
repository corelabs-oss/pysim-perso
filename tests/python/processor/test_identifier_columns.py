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
"""Structure-preserving identifier sequencing and duplicate-column sizing."""

import pytest

from pysim_perso.processor.process import DataFrameProcessor, DataProcessing


def _frame(rows):
    return DataFrameProcessor.generate_empty_dataframe(["ID"], rows)


# ------------------------------------------------------------------ #
# initialize_identifier_column — zero padding
# ------------------------------------------------------------------ #


def test_leading_zeros_are_preserved():
    # int() dropped these, shortening a 15-digit test-network IMSI to 13.
    df = _frame(3)
    DataFrameProcessor.initialize_identifier_column(df, "ID", "001010000000001")
    assert list(df["ID"]) == [
        "001010000000001",
        "001010000000002",
        "001010000000003",
    ]


def test_width_is_constant_across_the_batch():
    df = _frame(20)
    DataFrameProcessor.initialize_identifier_column(df, "ID", "000000000000998")
    assert {len(v) for v in df["ID"]} == {15}


def test_values_are_strings_not_integers():
    df = _frame(2)
    DataFrameProcessor.initialize_identifier_column(df, "ID", "0012")
    assert all(isinstance(v, str) for v in df["ID"])


def test_carry_within_the_suffix_is_allowed():
    df = _frame(3)
    DataFrameProcessor.initialize_identifier_column(df, "ID", "0098")
    assert list(df["ID"]) == ["0098", "0099", "0100"]


# ------------------------------------------------------------------ #
# initialize_identifier_column — prefix protection
# ------------------------------------------------------------------ #


def test_prefix_is_held_constant():
    df = _frame(3)
    DataFrameProcessor.initialize_identifier_column(
        df, "ID", "410092078615999", prefix_length=5
    )
    assert [v[:5] for v in df["ID"]] == ["41009"] * 3
    assert list(df["ID"]) == [
        "410092078615999",
        "410092078616000",
        "410092078616001",
    ]


def test_overflow_into_prefix_raises():
    # "410099999999998" + 4 rows previously became 410100000000000 silently,
    # moving the batch from MNC 09 to MNC 10.
    df = _frame(4)
    with pytest.raises(ValueError, match="overflows"):
        DataFrameProcessor.initialize_identifier_column(
            df, "ID", "410099999999998", prefix_length=5
        )


def test_exact_fit_to_suffix_boundary_is_allowed():
    df = _frame(2)
    DataFrameProcessor.initialize_identifier_column(
        df, "ID", "410099999999998", prefix_length=5
    )
    assert list(df["ID"]) == ["410099999999998", "410099999999999"]


def test_overflow_without_prefix_raises_on_width_growth():
    df = _frame(3)
    with pytest.raises(ValueError, match="overflows"):
        DataFrameProcessor.initialize_identifier_column(df, "ID", "998")


# ------------------------------------------------------------------ #
# initialize_identifier_column — input validation
# ------------------------------------------------------------------ #


@pytest.mark.parametrize("bad", ["41009207861599x", "", "12.5", "-123"])
def test_non_numeric_start_value_raises(bad):
    df = _frame(2)
    with pytest.raises(ValueError, match="numeric identifier"):
        DataFrameProcessor.initialize_identifier_column(df, "ID", bad)


@pytest.mark.parametrize("prefix_length", [-1, 4, 10])
def test_prefix_length_out_of_range_raises(prefix_length):
    df = _frame(2)
    with pytest.raises(ValueError, match="prefix_length"):
        DataFrameProcessor.initialize_identifier_column(
            df, "ID", "1234", prefix_length=prefix_length
        )


def test_initialize_column_still_returns_integers():
    # The original integer-based helper is unchanged and still used for
    # non-identifier columns.
    df = _frame(4)
    DataFrameProcessor.initialize_column(df, "ID", "100")
    assert list(df["ID"]) == [100, 101, 102, 103]


# ------------------------------------------------------------------ #
# ordered_entries — laser positions sort numerically
# ------------------------------------------------------------------ #


def test_numeric_keys_are_sorted_by_value():
    entries = DataProcessing.ordered_entries({"2": ["C"], "0": ["A"], "1": ["B"]})
    assert [e[0] for e in entries] == ["A", "B", "C"]


def test_two_digit_keys_do_not_sort_lexicographically():
    # "10" must follow "9", not sit between "1" and "2".
    param_dict = {str(i): [f"col{i}"] for i in [0, 1, 2, 9, 10, 11]}
    entries = DataProcessing.ordered_entries(param_dict)
    assert [e[0] for e in entries] == [
        "col0",
        "col1",
        "col2",
        "col9",
        "col10",
        "col11",
    ]


def test_non_numeric_keys_keep_insertion_order():
    param_dict = {"p2": ["B"], "p1": ["A"], "p3": ["C"]}
    entries = DataProcessing.ordered_entries(param_dict)
    assert [e[0] for e in entries] == ["B", "A", "C"]


def test_empty_dict_is_handled():
    assert DataProcessing.ordered_entries({}) == []


def test_extract_parameter_info_applies_numeric_ordering():
    params = {
        "1": ["IMSI", "Normal", "4-6"],
        "0": ["ICCID", "Normal", "1-3"],
    }
    renamed, _, _, classes, left, right = DataProcessing.extract_parameter_info(params)
    assert renamed == ["ICCID", "IMSI"]
    assert left == [1, 4] and right == [3, 6]
    assert classes == ["Normal", "Normal"]


# ------------------------------------------------------------------ #
# max_duplicate_suffix — replaces the hardcoded ceiling of 10
# ------------------------------------------------------------------ #


def test_no_duplicates_needs_no_suffixes():
    assert (
        DataProcessing.max_duplicate_suffix(["ICCID", "IMSI"], ["ICCID", "IMSI"]) == 0
    )


def test_suffix_is_derived_from_headers():
    headers = ["ICCID", "ICCID1", "ICCID2", "ICCID3"]
    assert DataProcessing.max_duplicate_suffix(headers, ["ICCID"]) == 3


def test_more_than_ten_duplicates_supported():
    headers = ["ICCID"] + [f"ICCID{i}" for i in range(1, 12)]
    assert DataProcessing.max_duplicate_suffix(headers, ["ICCID"]) == 11


def test_columns_ending_in_digits_are_not_misparsed():
    # KIC1 is a real column, so "KIC11" is KIC1 + suffix 1, not KIC + 11.
    columns = ["KIC1", "KIC2", "ICCID"]
    assert DataProcessing.max_duplicate_suffix(["KIC1", "KIC11"], columns) == 1


def test_real_column_names_are_skipped():
    columns = ["KIC1", "KID1", "KIK1"]
    assert DataProcessing.max_duplicate_suffix(["KIC1", "KID1", "KIK1"], columns) == 0


def test_unrelated_header_is_ignored():
    assert DataProcessing.max_duplicate_suffix(["UNKNOWN9"], ["ICCID"]) == 0


# ------------------------------------------------------------------ #
# generate_empty_dataframe
# ------------------------------------------------------------------ #


def test_empty_dataframe_keeps_columns_and_dtype():
    df = DataFrameProcessor.generate_empty_dataframe(["A", "B"], "3")
    assert list(df.columns) == ["A", "B"]
    assert df.shape == (3, 2)
    assert (df == 0).all().all()


def test_empty_dataframe_accepts_int_rows():
    assert len(DataFrameProcessor.generate_empty_dataframe(["A"], 7)) == 7
