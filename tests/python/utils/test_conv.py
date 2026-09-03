# test_utils.py
import pytest

from pysim_perso.utils import dict_2_list, list_2_dict


def test_list_2_dict_basic():
    data = ["A", "B", "C"]
    result = list_2_dict(data)
    assert isinstance(result, dict)
    assert result == {
        "0": ["A", "Normal", "0-31"],
        "1": ["B", "Normal", "0-31"],
        "2": ["C", "Normal", "0-31"],
    }


def test_dict_2_list_basic():
    d = {
        "0": ["A", "Normal", "0-31"],
        "1": ["B", "Normal", "0-31"],
        "2": ["C", "Normal", "0-31"],
    }
    result = dict_2_list(d)
    assert result == ["A", "B", "C"]


def test_round_trip():
    original = ["X", "Y", "Z"]
    converted = list_2_dict(original)
    back = dict_2_list(converted)
    assert back == original


def test_empty_inputs():
    assert list_2_dict([]) == {}
    assert dict_2_list({}) == []


def test_non_string_values():
    data = [123, 45.6, True]
    d = list_2_dict(data)
    back = dict_2_list(d)
    assert back == data
