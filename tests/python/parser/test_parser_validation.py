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
"""Character-set and structural validation of the configuration.

Every case here previously passed configuration validation and then failed
somewhere deep in the pipeline — or, worse, silently produced wrong output.
"""

import copy

import pytest
from pydantic import ValidationError

from pysim_perso.parser.utils import json_loader_2_ConfigHolder

VALID_CONFIG = {
    "DISP": {
        "elect_data_sep": ",",
        "server_data_sep": ",",
        "graph_data_sep": ",",
        "K4": "A" * 64,
        "op": "A" * 32,
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
        "laser_variables": {"0": ["ICCID", "Normal", "0-18"]},
    },
}


@pytest.fixture
def cfg():
    return copy.deepcopy(VALID_CONFIG)


# ------------------------------------------------------------------ #
# Character-set validation — these used to crash inside int()/binascii
# ------------------------------------------------------------------ #


@pytest.mark.parametrize(
    "field,value",
    [
        ("imsi", "41009207861599x"),  # 15 chars but not numeric
        ("iccid", "78600786999999800XY"),
        ("pin1", "abcd"),
        ("pin2", "12a4"),
        ("puk1", "1234567x"),
        ("op", "ZZ001111000022220000333300004444"),  # 32 chars, not hex
        ("K4", "Z" * 64),
    ],
)
def test_non_conforming_charset_rejected(cfg, field, value):
    cfg["DISP"][field] = value
    with pytest.raises(ValidationError):
        json_loader_2_ConfigHolder(cfg)


def test_adm_rejects_non_ascii(cfg):
    # s2h() formats each char with "%02x"; a code point above 0x7E silently
    # produces a wrong-length encoded field.
    cfg["DISP"]["adm1"] = "ADMé123"
    with pytest.raises(ValidationError):
        json_loader_2_ConfigHolder(cfg)


def test_adm_allows_printable_alphanumeric(cfg):
    cfg["DISP"]["adm1"] = "ADM12345"
    assert json_loader_2_ConfigHolder(cfg).DISP.adm1 == "ADM12345"


# ------------------------------------------------------------------ #
# K4 must land on a real AES key size
# ------------------------------------------------------------------ #


@pytest.mark.parametrize("hex_len", [32, 48, 64])
def test_k4_valid_aes_key_sizes_accepted(cfg, hex_len):
    cfg["DISP"]["K4"] = "A" * hex_len
    assert len(json_loader_2_ConfigHolder(cfg).DISP.K4) == hex_len


@pytest.mark.parametrize("hex_len", [34, 40, 46, 50, 62])
def test_k4_invalid_aes_key_sizes_rejected(cfg, hex_len):
    # Previously accepted, then raised "Incorrect AES key length" from PyCryptodome.
    cfg["DISP"]["K4"] = "A" * hex_len
    with pytest.raises(ValidationError, match="32, 48 or 64"):
        json_loader_2_ConfigHolder(cfg)


# ------------------------------------------------------------------ #
# Output column selections must name real columns
# ------------------------------------------------------------------ #


@pytest.mark.parametrize("field", ["data_variables", "server_variables"])
def test_unknown_output_column_rejected(cfg, field):
    cfg["PARAMETERS"][field] = ["IMSI", "CELL_ID"]
    with pytest.raises(ValidationError, match="unknown column"):
        json_loader_2_ConfigHolder(cfg)


def test_lowercase_column_names_rejected(cfg):
    # Column lookup is case-sensitive; lowercase names KeyError at output time.
    cfg["PARAMETERS"]["data_variables"] = ["imsi", "iccid"]
    with pytest.raises(ValidationError, match="unknown column"):
        json_loader_2_ConfigHolder(cfg)


# ------------------------------------------------------------------ #
# laser_variables structure
# ------------------------------------------------------------------ #


def test_laser_key_must_be_integer_position(cfg):
    cfg["PARAMETERS"]["laser_variables"] = {"laser1": ["ICCID", "Normal", "0-3"]}
    with pytest.raises(ValidationError, match="integer position"):
        json_loader_2_ConfigHolder(cfg)


@pytest.mark.parametrize(
    "entry", [["ICCID", "Normal"], ["ICCID"], ["ICCID", "Normal", "0-3", "extra"]]
)
def test_laser_entry_must_have_three_elements(cfg, entry):
    cfg["PARAMETERS"]["laser_variables"] = {"0": entry}
    with pytest.raises(ValidationError, match="exactly 3 elements"):
        json_loader_2_ConfigHolder(cfg)


def test_laser_unknown_column_rejected(cfg):
    cfg["PARAMETERS"]["laser_variables"] = {"0": ["CELL_ID", "Normal", "0-3"]}
    with pytest.raises(ValidationError, match="unknown column"):
        json_loader_2_ConfigHolder(cfg)


def test_laser_reversed_range_rejected(cfg):
    # A reversed range silently produced an empty laser field.
    cfg["PARAMETERS"]["laser_variables"] = {"0": ["IMSI", "Normal", "5-3"]}
    with pytest.raises(ValidationError, match="reversed"):
        json_loader_2_ConfigHolder(cfg)


@pytest.mark.parametrize("bad_range", ["garbage", "", "0", "0-", "-3", "a-b", "0:3"])
def test_laser_unparseable_range_rejected(cfg, bad_range):
    # split_range() silently fell back to (0, 32) for anything it couldn't parse.
    cfg["PARAMETERS"]["laser_variables"] = {"0": ["IMSI", "Normal", bad_range]}
    with pytest.raises(ValidationError, match="must be"):
        json_loader_2_ConfigHolder(cfg)


def test_laser_equal_bounds_accepted(cfg):
    cfg["PARAMETERS"]["laser_variables"] = {"0": ["IMSI", "Normal", "3-3"]}
    assert json_loader_2_ConfigHolder(cfg).PARAMETERS.laser_variables["0"][2] == "3-3"


def test_empty_laser_variables_accepted(cfg):
    # Legitimate when graph output is disabled.
    cfg["PARAMETERS"]["laser_variables"] = {}
    assert json_loader_2_ConfigHolder(cfg).PARAMETERS.laser_variables == {}


# ------------------------------------------------------------------ #
# No regression on the shipped example config
# ------------------------------------------------------------------ #


def test_valid_config_still_accepted(cfg):
    holder = json_loader_2_ConfigHolder(cfg)
    assert holder.DISP.imsi == "111111111121111"
