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
"""The ``prod_check`` config flag is honoured.

The flag was previously parsed and stored but never read, so the validation it
advertises never ran.
"""

import copy

import pytest

from gsm_data_generator import DATAGENError
from gsm_data_generator.error import ConfigValidationError
from gsm_data_generator.executor.script import DataGenerationScript
from gsm_data_generator.globals.parameters import DataFrames, Parameters
from gsm_data_generator.parser.utils import json_loader_2_ConfigHolder

_BASE_CONFIG = {
    "DISP": {
        "elect_data_sep": ",",
        "server_data_sep": ",",
        "graph_data_sep": ",",
        "K4": "A" * 32,
        "op": "A" * 32,
        "imsi": "111111111121111",
        "iccid": "111111111121221111",
        "pin1": "1111",
        "puk1": "11111111",
        "pin2": "1111",
        "puk2": "11111111",
        "adm1": "11111111",
        "adm6": "11111111",
        "size": 3,
        "prod_check": True,
        "elect_check": True,
        "graph_check": False,
        "server_check": False,
        "pin1_fix": True,
        "puk1_fix": True,
        "pin2_fix": True,
        "puk2_fix": True,
        "adm1_fix": False,
        "adm6_fix": False,
    },
    "PATHS": {
        "FILE_NAME": "test_file",
        "OUTPUT_FILES_DIR": "output",
        "OUTPUT_FILES_LASER_EXT": "laser",
    },
    "PARAMETERS": {
        "server_variables": ["IMSI"],
        "data_variables": ["IMSI", "ICCID", "KI", "OPC"],
        "laser_variables": {"0": ["ICCID", "Normal", "0-18"]},
    },
}


@pytest.fixture(autouse=True)
def reset_singletons():
    Parameters._Parameters__instance = None  # type: ignore[attr-defined]
    DataFrames._DataFrames__instance = None  # type: ignore[attr-defined]
    yield
    Parameters._Parameters__instance = None  # type: ignore[attr-defined]
    DataFrames._DataFrames__instance = None  # type: ignore[attr-defined]


def _script(config):
    s = DataGenerationScript(json_loader_2_ConfigHolder(config))
    s.json_to_global_params()
    return s


def test_valid_config_passes_prod_check():
    result, _ = _script(copy.deepcopy(_BASE_CONFIG)).generate_all_data()
    assert len(result["ELECT"]) == 3


def test_prod_check_rejects_invalid_param():
    s = _script(copy.deepcopy(_BASE_CONFIG))
    s.params.IMSI = "123"  # bypasses the parser, as a GUI caller could
    with pytest.raises(ConfigValidationError, match="IMSI"):
        s.generate_all_data()


def test_prod_check_reports_every_failure_not_just_the_first():
    s = _script(copy.deepcopy(_BASE_CONFIG))
    s.params.IMSI = "123"
    s.params.OP = ""
    s.params.PUK1 = "12"
    with pytest.raises(ConfigValidationError) as exc:
        s.generate_all_data()
    message = str(exc.value)
    assert "IMSI" in message and "OP" in message and "PUK1" in message


def test_prod_check_disabled_skips_validation():
    config = copy.deepcopy(_BASE_CONFIG)
    config["DISP"]["prod_check"] = False
    s = _script(config)
    s.params.ADM1 = "not-eight"  # invalid, but validation is opted out
    result, _ = s.generate_all_data()
    assert len(result["ELECT"]) == 3


def test_prod_check_ignores_dicts_for_disabled_outputs():
    # SERVER is disabled, so an empty SERVER_DICT must not fail validation.
    s = _script(copy.deepcopy(_BASE_CONFIG))
    assert s.params.SERVER_CHECK is False
    s.params.SERVER_DICT = {}
    result, _ = s.generate_all_data()
    assert "SERVER" not in result


def test_config_validation_error_is_catchable_as_value_error():
    # Callers that already catch ValueError around config handling keep working.
    s = _script(copy.deepcopy(_BASE_CONFIG))
    s.params.IMSI = "123"
    with pytest.raises(ValueError):
        s.generate_all_data()


def test_config_validation_error_is_a_datagen_error():
    assert issubclass(ConfigValidationError, DATAGENError)


# ------------------------------------------------------------------ #
# validate_params() reports detail; check_params() keeps its old contract
# ------------------------------------------------------------------ #


def test_validate_params_returns_empty_list_when_valid():
    s = _script(copy.deepcopy(_BASE_CONFIG))
    assert s.params.validate_params() == []


def test_validate_params_does_not_raise_on_empty_values():
    p = Parameters.get_instance()
    # Every field left at its "" default — must report failures, not raise.
    assert len(p.validate_params()) > 0


def test_check_params_still_returns_bool():
    s = _script(copy.deepcopy(_BASE_CONFIG))
    assert isinstance(s.params.check_params(), bool)
