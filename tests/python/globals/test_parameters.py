# test_parameters.py
import pytest
import pandas as pd
import gsm_data_generator
from gsm_data_generator.globals import Parameters, DataFrames


@pytest.fixture
def params():
    # Always reset singleton
    Parameters._Parameters__instance = None  # type: ignore
    DataFrames._DataFrames__instance = None  # type: ignore
    return Parameters.get_instance()


def test_singleton(params):
    p2 = Parameters.get_instance()
    assert params is p2  # both should be same instance


def test_get_basic_fields(params):
    params.PIN1 = "1234"
    assert params.PIN1 == "1234"

    params.PUK1 = "12345678"
    assert params.PUK1 == "12345678"

    params.OP = "A" * 32
    assert len(params.OP) == 32

    params.K4 = "B" * 64
    assert len(params.K4) == 64


def test_is_valid_rules(params):
    assert Parameters.is_valid("123456789012345", "IMSI") is True
    assert Parameters.is_valid("1234", "PIN1") is True
    assert Parameters.is_valid("12345678", "PUK1") is True
    assert Parameters.is_valid("A" * 32, "OP") is True
    assert Parameters.is_valid("B" * 64, "K4") is True
    assert Parameters.is_valid({"k": "v"}, "DICT") is True
    assert Parameters.is_valid(100, "SIZE") is True
    assert Parameters.is_valid("bad", "IMSI") is False


def test_is_valid_df(params):
    df = pd.DataFrame()
    assert Parameters.is_valid_df(df, "DF") is True

    df2 = pd.DataFrame({"a": [1, 2]})
    assert Parameters.is_valid_df(df2, "DF") is False


def test_get_all_params_dict(params):
    params.PIN1 = "1234"
    params.PUK1 = "12345678"
    params.PIN2 = "5678"
    params.PUK2 = "87654321"
    params.ADM1 = "11111111"
    params.ADM6 = "22222222"
    params.OP = "A" * 32
    params.K4 = "B" * 64
    params.ACC = "99"
    params.DATA_SIZE = "256"
    params.INPUT_PATH = "/tmp"

    d = params.get_all_params_dict()
    assert "ICCID" in d
    assert "PIN1" in d
    assert isinstance(d, dict)


def test_check_params_production(params):
    # Production mode (False means Production in your code)
    # params.PRODUCTION_CHECK(True)

    params.PIN1 = "1234"
    params.PIN1 = "1234"
    params.PUK1 = "12345678"
    params.PIN2 = "5678"
    params.PUK2 = "87654321"
    params.ADM1 = "11111111"
    params.ADM6 = "22222222"
    params.OP = "A" * 32
    params.K4 = "B" * 64
    params.ELECT_DICT = {"a": 1}
    params.GRAPH_DICT = {"b": 2}

    assert params.check_params() is False


def test_check_params_demo(params):
    # Demo mode (True means Demo in your code)
    # params.PRODUCTION_CHECK(True)

    params.IMSI = "123456789012345"
    params.ICCID = "1234567890123456789"
    params.DATA_SIZE = "100"
    params.PIN1 = "1234"
    params.PUK1 = "12345678"
    params.PIN2 = "5678"
    params.PUK2 = "87654321"
    params.ADM1 = "11111111"
    params.ADM6 = "22222222"
    params.OP = "A" * 32
    params.K4 = "B" * 64
    params.ELECT_DICT = {"a": 1}
    params.GRAPH_DICT = {"b": 2}

    assert params.check_params() is True
