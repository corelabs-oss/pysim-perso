import pytest
from pysim_perso.processor import DataProcessing


def test_split_range_valid():
    assert DataProcessing.split_range("5-10") == (5, 10)


def test_split_range_invalid():
    # no dash → default
    assert DataProcessing.split_range("55") == (0, 32)
    # too short
    assert DataProcessing.split_range("-") == (0, 32)
    # empty
    assert DataProcessing.split_range("") == (0, 32)


def test_extract_ranges():
    left, right = DataProcessing.extract_ranges(["1-5", "10-15"])
    assert left == [1, 10]
    assert right == [5, 15]


def test_find_duplicates():
    items = ["A", "B", "A", "C", "B", "D"]
    result = DataProcessing.find_duplicates(items)
    assert set(result) == {"A", "B"}


def test_append_count_to_duplicates():
    input_list = ["X", "Y", "X", "X", "Y"]
    result = DataProcessing.append_count_to_duplicates(input_list)
    # First "X" → X, second "X" → X1, third "X" → X2
    assert result.count("X") == 1
    assert "X1" in result
    assert "X2" in result
    assert result.count("Y") == 1
    assert "Y1" in result


def test_extract_parameter_info():
    params = {
        "p1": ["val", "classA", "1-3"],
        "p2": ["val", "classB", "4-6"],
        "p3": ["other", "classC", "7-8"],
    }
    renamed, duplicates, unique, classes, left, right = (
        DataProcessing.extract_parameter_info(params)
    )

    assert "val" in renamed
    assert "val1" in renamed  # duplicate renamed
    assert "other" in renamed

    assert duplicates == ["val"]
    assert unique == {"val", "other"}
    assert classes == ["classA", "classB", "classC"]
    assert left == [1, 4, 7]
    assert right == [3, 6, 8]
