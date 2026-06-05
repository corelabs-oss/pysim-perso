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
import copy
import json

import pytest
from pydantic import ValidationError

from gsm_data_generator.parser.utils import (
    ConfigHolder,
    json_loader,
    json_loader_2_ConfigHolder,
)

# ------------------------------------------------------------------ #
# Minimal valid config — mutated per test to trigger specific errors
# ------------------------------------------------------------------ #
VALID_CONFIG = {
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
        "pin2": "1111",
        "puk2": "11111111",
        "adm1": "11111111",
        "adm6": "11111111",
        "size": 5,
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
        "data_variables": ["IMSI", "ICCID"],
        "laser_variables": {"0": ["ICCID", "Normal", "0-20"]},
    },
}


@pytest.fixture
def base_config():
    return copy.deepcopy(VALID_CONFIG)


# ------------------------------------------------------------------ #
# json_loader_2_ConfigHolder — happy path
# ------------------------------------------------------------------ #

def test_valid_dict_returns_config_holder(base_config):
    result = json_loader_2_ConfigHolder(base_config)
    assert isinstance(result, ConfigHolder)


def test_valid_json_string_returns_config_holder(base_config):
    json_str = json.dumps(base_config)
    result = json_loader_2_ConfigHolder(json_str)
    assert isinstance(result, ConfigHolder)


def test_config_holder_fields_match_input(base_config):
    result = json_loader_2_ConfigHolder(base_config)
    assert result.DISP.imsi == "111111111121111"
    assert result.DISP.pin1 == "1111"
    assert result.DISP.size == 5
    assert result.PATHS.FILE_NAME == "test_file"
    assert "IMSI" in result.PARAMETERS.data_variables


# ------------------------------------------------------------------ #
# json_loader_2_ConfigHolder — bad input type
# ------------------------------------------------------------------ #

def test_bad_json_string_raises_value_error():
    with pytest.raises(ValueError, match="Invalid JSON string"):
        json_loader_2_ConfigHolder("{not: valid json}")


def test_wrong_input_type_raises_value_error():
    with pytest.raises(ValueError, match="Input must be"):
        json_loader_2_ConfigHolder(42)  # type: ignore


def test_none_input_raises_value_error():
    with pytest.raises(ValueError, match="Input must be"):
        json_loader_2_ConfigHolder(None)  # type: ignore


def test_list_input_raises_value_error():
    with pytest.raises(ValueError, match="Input must be"):
        json_loader_2_ConfigHolder([1, 2, 3])  # type: ignore


# ------------------------------------------------------------------ #
# json_loader_2_ConfigHolder — missing required fields
# ------------------------------------------------------------------ #

def test_missing_disp_section_raises(base_config):
    del base_config["DISP"]
    with pytest.raises((ValidationError, KeyError, TypeError)):
        json_loader_2_ConfigHolder(base_config)


def test_missing_paths_section_raises(base_config):
    del base_config["PATHS"]
    with pytest.raises((ValidationError, KeyError, TypeError)):
        json_loader_2_ConfigHolder(base_config)


def test_missing_parameters_section_raises(base_config):
    del base_config["PARAMETERS"]
    with pytest.raises((ValidationError, KeyError, TypeError)):
        json_loader_2_ConfigHolder(base_config)


def test_missing_imsi_raises_validation_error(base_config):
    del base_config["DISP"]["imsi"]
    with pytest.raises(ValidationError):
        json_loader_2_ConfigHolder(base_config)


def test_missing_pin1_raises_validation_error(base_config):
    del base_config["DISP"]["pin1"]
    with pytest.raises(ValidationError):
        json_loader_2_ConfigHolder(base_config)


# ------------------------------------------------------------------ #
# json_loader_2_ConfigHolder — field length / value constraints
# ------------------------------------------------------------------ #

def test_imsi_too_short_raises_validation_error(base_config):
    base_config["DISP"]["imsi"] = "12345678901234"  # 14 chars, need 15
    with pytest.raises(ValidationError):
        json_loader_2_ConfigHolder(base_config)


def test_imsi_too_long_raises_validation_error(base_config):
    base_config["DISP"]["imsi"] = "1234567890123456"  # 16 chars
    with pytest.raises(ValidationError):
        json_loader_2_ConfigHolder(base_config)


def test_iccid_too_short_raises_validation_error(base_config):
    base_config["DISP"]["iccid"] = "12345678901234567"  # 17 chars, need 18-19
    with pytest.raises(ValidationError):
        json_loader_2_ConfigHolder(base_config)


def test_pin_too_short_raises_validation_error(base_config):
    base_config["DISP"]["pin1"] = "123"  # 3 chars, need 4
    with pytest.raises(ValidationError):
        json_loader_2_ConfigHolder(base_config)


def test_pin_too_long_raises_validation_error(base_config):
    base_config["DISP"]["pin1"] = "12345"  # 5 chars, need 4
    with pytest.raises(ValidationError):
        json_loader_2_ConfigHolder(base_config)


def test_puk_too_short_raises_validation_error(base_config):
    base_config["DISP"]["puk1"] = "1234567"  # 7 chars, need 8
    with pytest.raises(ValidationError):
        json_loader_2_ConfigHolder(base_config)


def test_k4_too_short_raises_validation_error(base_config):
    base_config["DISP"]["K4"] = "AAAA"  # too short, need >=32
    with pytest.raises(ValidationError):
        json_loader_2_ConfigHolder(base_config)


def test_op_wrong_length_raises_validation_error(base_config):
    base_config["DISP"]["op"] = "AAAA"  # too short, need exactly 32
    with pytest.raises(ValidationError):
        json_loader_2_ConfigHolder(base_config)


def test_size_zero_raises_validation_error(base_config):
    base_config["DISP"]["size"] = 0  # must be >= 1
    with pytest.raises(ValidationError):
        json_loader_2_ConfigHolder(base_config)


def test_size_negative_raises_validation_error(base_config):
    base_config["DISP"]["size"] = -1
    with pytest.raises(ValidationError):
        json_loader_2_ConfigHolder(base_config)


def test_empty_separator_raises_validation_error(base_config):
    base_config["DISP"]["elect_data_sep"] = ""  # min_length=1
    with pytest.raises(ValidationError):
        json_loader_2_ConfigHolder(base_config)


# ------------------------------------------------------------------ #
# json_loader — file-based loading
# ------------------------------------------------------------------ #

def test_json_loader_file_not_found():
    with pytest.raises(FileNotFoundError):
        json_loader("definitely_does_not_exist_xyz.json")


def test_json_loader_invalid_json_content(tmp_path):
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("{not: valid json}", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        json_loader(str(bad_file))


def test_json_loader_valid_file_returns_config_holder(tmp_path):
    valid_file = tmp_path / "settings.json"
    valid_file.write_text(json.dumps(VALID_CONFIG), encoding="utf-8")
    result = json_loader(str(valid_file))
    assert isinstance(result, ConfigHolder)
    assert result.DISP.imsi == "111111111121111"
