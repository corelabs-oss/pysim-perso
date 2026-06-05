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
"""Unit tests for individual DataGenerationScript methods."""
import pytest

from gsm_data_generator.executor.script import DataGenerationScript
from gsm_data_generator.globals.parameters import Parameters, DataFrames
from gsm_data_generator.parser.utils import json_loader_2_ConfigHolder

_BASE_CONFIG = {
    "DISP": {
        "elect_data_sep": ",",
        "server_data_sep": ",",
        "graph_data_sep": ",",
        "K4": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
        "op": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
        "imsi": "111111111121111",
        "iccid": "111111111121221111",
        "pin1": "1111",
        "puk1": "11111111",
        "pin2": "2222",
        "puk2": "22222222",
        "adm1": "33333333",
        "adm6": "44444444",
        "size": 3,
        "prod_check": True,
        "elect_check": True,
        "graph_check": True,
        "server_check": False,
        "pin1_fix": True,
        "puk1_fix": True,
        "pin2_fix": True,
        "puk2_fix": True,
        "adm1_fix": True,
        "adm6_fix": True,
    },
    "PATHS": {
        "FILE_NAME": "test",
        "OUTPUT_FILES_DIR": "out",
        "OUTPUT_FILES_LASER_EXT": "laser",
    },
    "PARAMETERS": {
        "server_variables": ["IMSI", "EKI"],
        "data_variables": [
            "IMSI", "ICCID", "PIN1", "PUK1", "PIN2", "PUK2",
            "ADM1", "ADM6", "KI", "OPC", "ACC",
            "KIC1", "KID1", "KIK1", "KIC2", "KID2", "KIK2",
            "KIC3", "KID3", "KIK3",
        ],
        "laser_variables": {
            "0": ["ICCID", "Normal", "0-20"],
            "1": ["ICCID", "Normal", "0-3"],
            "2": ["PIN1", "Normal", "0-3"],
            "3": ["IMSI", "Normal", "0-5"],
            "4": ["IMSI", "Normal", "6-15"],
        },
    },
}


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset both singletons before every test so state doesn't leak."""
    Parameters._Parameters__instance = None   # type: ignore[attr-defined]
    DataFrames._DataFrames__instance = None    # type: ignore[attr-defined]
    yield
    Parameters._Parameters__instance = None   # type: ignore[attr-defined]
    DataFrames._DataFrames__instance = None    # type: ignore[attr-defined]


@pytest.fixture
def script():
    config = json_loader_2_ConfigHolder(_BASE_CONFIG)
    s = DataGenerationScript(config)
    s.json_to_global_params()
    return s


# ------------------------------------------------------------------ #
# json_to_global_params
# ------------------------------------------------------------------ #

def test_json_to_global_params_sets_imsi(script):
    p = Parameters.get_instance()
    assert p.IMSI == "111111111121111"


def test_json_to_global_params_sets_k4(script):
    p = Parameters.get_instance()
    assert p.K4 == "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"


def test_json_to_global_params_sets_separators(script):
    p = Parameters.get_instance()
    assert p.ELECT_SEP == ","
    assert p.SERVER_SEP == ","


def test_json_to_global_params_sets_check_flags(script):
    p = Parameters.get_instance()
    assert p.ELECT_CHECK is True
    assert p.GRAPH_CHECK is True
    assert p.SERVER_CHECK is False


def test_json_to_global_params_sets_rand_flags(script):
    p = Parameters.get_instance()
    # _BASE_CONFIG has all _fix=True, which maps to *_RAND=True (use fixed value)
    assert p.PIN1_RAND is True
    assert p.ADM1_RAND is True


# ------------------------------------------------------------------ #
# generate_pin — fixed vs. random branching
# ------------------------------------------------------------------ #

def test_generate_pin_returns_fixed_value_when_rand_true(script):
    p = Parameters.get_instance()
    p.PIN1 = "9876"
    p.PIN1_RAND = True
    assert script.generate_pin("PIN1") == "9876"


def test_generate_pin_returns_random_4_digits_when_rand_false(script):
    p = Parameters.get_instance()
    p.PIN1_RAND = False
    result = script.generate_pin("PIN1")
    assert len(result) == 4
    assert result.isdigit()


def test_generate_pin_random_differs_from_fixed(script):
    """Random PIN should not be locked to the stored value."""
    p = Parameters.get_instance()
    p.PIN1 = "0000"
    p.PIN1_RAND = False
    # Generate multiple times — at least one should differ from "0000"
    results = {script.generate_pin("PIN1") for _ in range(20)}
    assert len(results) > 1 or results != {"0000"}


def test_generate_pin2_fixed(script):
    p = Parameters.get_instance()
    p.PIN2 = "5678"
    p.PIN2_RAND = True
    assert script.generate_pin("PIN2") == "5678"


# ------------------------------------------------------------------ #
# generate_puk — fixed vs. random branching
# ------------------------------------------------------------------ #

def test_generate_puk_returns_fixed_value_when_rand_true(script):
    p = Parameters.get_instance()
    p.PUK1 = "87654321"
    p.PUK1_RAND = True
    assert script.generate_puk("PUK1") == "87654321"


def test_generate_puk_returns_random_8_digits_when_rand_false(script):
    p = Parameters.get_instance()
    p.PUK1_RAND = False
    result = script.generate_puk("PUK1")
    assert len(result) == 8
    assert result.isdigit()


def test_generate_puk2_fixed(script):
    p = Parameters.get_instance()
    p.PUK2 = "11223344"
    p.PUK2_RAND = True
    assert script.generate_puk("PUK2") == "11223344"


# ------------------------------------------------------------------ #
# generate_adm — fixed vs. random branching
# ------------------------------------------------------------------ #

def test_generate_adm_returns_fixed_value_when_rand_true(script):
    p = Parameters.get_instance()
    p.ADM1 = "ABCD1234"
    p.ADM1_RAND = True
    assert script.generate_adm("ADM1") == "ABCD1234"


def test_generate_adm_returns_random_8_digits_when_rand_false(script):
    p = Parameters.get_instance()
    p.ADM1_RAND = False
    result = script.generate_adm("ADM1")
    assert len(result) == 8
    assert result.isdigit()


def test_generate_adm6_fixed(script):
    p = Parameters.get_instance()
    p.ADM6 = "FFFFAAAA"
    p.ADM6_RAND = True
    assert script.generate_adm("ADM6") == "FFFFAAAA"


# ------------------------------------------------------------------ #
# generate_eki / generate_opc
# ------------------------------------------------------------------ #

def test_generate_eki_returns_32_char_uppercase_hex(script):
    ki = "A" * 32
    result = script.generate_eki(ki)
    assert len(result) == 32
    assert result == result.upper()
    assert all(c in "0123456789ABCDEF" for c in result)


def test_generate_opc_returns_32_char_uppercase_hex(script):
    ki = "B" * 32
    result = script.generate_opc(ki)
    assert len(result) == 32
    assert result == result.upper()
    assert all(c in "0123456789ABCDEF" for c in result)


def test_generate_eki_is_deterministic_for_same_inputs(script):
    ki = "C" * 32
    assert script.generate_eki(ki) == script.generate_eki(ki)


def test_generate_opc_is_deterministic_for_same_inputs(script):
    ki = "D" * 32
    assert script.generate_opc(ki) == script.generate_opc(ki)


def test_generate_eki_differs_for_different_ki(script):
    assert script.generate_eki("A" * 32) != script.generate_eki("B" * 32)


# ------------------------------------------------------------------ #
# generate_initial_data
# ------------------------------------------------------------------ #

def test_generate_initial_data_demo_returns_df_and_keys(script):
    df, keys = script.generate_initial_data(is_demo=True)
    assert not df.empty
    assert "k4" in keys
    assert "op" in keys


def test_generate_initial_data_demo_keys_match_params(script):
    _, keys = script.generate_initial_data(is_demo=True)
    p = Parameters.get_instance()
    assert keys["k4"] == p.K4
    assert keys["op"] == p.OP


def test_generate_initial_data_non_demo_raises_runtime_error(script):
    with pytest.raises(RuntimeError, match="not yet implemented"):
        script.generate_initial_data(is_demo=False)


# ------------------------------------------------------------------ #
# generate_all_data — error cases
# ------------------------------------------------------------------ #

def test_generate_all_data_raises_when_enabled_dict_is_empty(script):
    p = Parameters.get_instance()
    p.ELECT_CHECK = True
    p.ELECT_DICT = {}  # enabled but empty dict
    with pytest.raises(ValueError, match="ELECT"):
        script.generate_all_data()


def test_generate_all_data_raises_when_server_dict_missing(script):
    p = Parameters.get_instance()
    p.SERVER_CHECK = True
    p.SERVER_DICT = {}
    with pytest.raises(ValueError, match="SERVER"):
        script.generate_all_data()


def test_generate_all_data_skips_disabled_output_types(script):
    p = Parameters.get_instance()
    p.SERVER_CHECK = False
    result_dfs, _ = script.generate_all_data()
    assert "SERVER" not in result_dfs


def test_generate_all_data_returns_correct_row_count(script):
    p = Parameters.get_instance()
    result_dfs, _ = script.generate_all_data()
    expected_rows = int(p.DATA_SIZE)
    for df in result_dfs.values():
        assert len(df) == expected_rows
