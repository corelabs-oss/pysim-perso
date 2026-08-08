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
"""End-to-end behaviour of identifier sequencing and laser column assembly."""

import copy

import pytest

from gsm_data_generator.algorithm.encode import EncodingUtils
from gsm_data_generator.executor.script import DataGenerationScript
from gsm_data_generator.globals.parameters import DataFrames, Parameters
from gsm_data_generator.parser.utils import json_loader_2_ConfigHolder

_BASE = {
    "DISP": {
        "elect_data_sep": ",",
        "server_data_sep": ",",
        "graph_data_sep": ",",
        "K4": "A" * 32,
        "op": "A" * 32,
        "imsi": "410092078615999",
        "iccid": "111111111121221111",
        "pin1": "1111",
        "puk1": "11111111",
        "pin2": "1111",
        "puk2": "11111111",
        "adm1": "11111111",
        "adm6": "11111111",
        "size": 3,
        "prod_check": True,
        "elect_check": False,
        "graph_check": False,
        "server_check": True,
        "pin1_fix": True,
        "puk1_fix": True,
        "pin2_fix": True,
        "puk2_fix": True,
        "adm1_fix": False,
        "adm6_fix": False,
    },
    "PATHS": {
        "FILE_NAME": "f",
        "OUTPUT_FILES_DIR": "out",
        "OUTPUT_FILES_LASER_EXT": "laser",
    },
    "PARAMETERS": {
        "server_variables": ["IMSI", "ICCID"],
        "data_variables": ["IMSI", "ICCID"],
        "laser_variables": {"0": ["ICCID", "Normal", "0-17"]},
    },
}


@pytest.fixture(autouse=True)
def reset_singletons():
    Parameters._Parameters__instance = None  # type: ignore[attr-defined]
    DataFrames._DataFrames__instance = None  # type: ignore[attr-defined]
    yield
    Parameters._Parameters__instance = None  # type: ignore[attr-defined]
    DataFrames._DataFrames__instance = None  # type: ignore[attr-defined]


def run(config):
    s = DataGenerationScript(json_loader_2_ConfigHolder(config))
    s.json_to_global_params()
    return s.generate_all_data()[0]


# ------------------------------------------------------------------ #
# IMSI structure is preserved through the pipeline
# ------------------------------------------------------------------ #


def test_imsi_keeps_full_width_and_leading_zeros():
    cfg = copy.deepcopy(_BASE)
    cfg["DISP"]["imsi"] = "001010000000001"  # MCC 001, the test-network code
    result = run(cfg)
    values = result["SERVER"]["IMSI"].tolist()
    assert values == ["001010000000001", "001010000000002", "001010000000003"]
    assert all(len(v) == 15 for v in values)


def test_iccid_keeps_leading_zeros():
    cfg = copy.deepcopy(_BASE)
    cfg["DISP"]["iccid"] = "001007869999998000"
    result = run(cfg)
    assert result["SERVER"]["ICCID"].tolist() == [
        "001007869999998000",
        "001007869999998001",
        "001007869999998002",
    ]


def test_msin_overflow_into_mnc_is_rejected():
    cfg = copy.deepcopy(_BASE)
    cfg["DISP"]["imsi"] = "410099999999998"  # 2 left before the MNC carries
    cfg["DISP"]["size"] = 4
    with pytest.raises(RuntimeError, match="overflow"):
        run(cfg)


def test_batch_inside_the_msin_is_unaffected():
    cfg = copy.deepcopy(_BASE)
    cfg["DISP"]["imsi"] = "410092078615999"
    result = run(cfg)
    assert result["SERVER"]["IMSI"].tolist() == [
        "410092078615999",
        "410092078616000",
        "410092078616001",
    ]


def test_mcc_and_mnc_are_constant_across_a_large_batch():
    cfg = copy.deepcopy(_BASE)
    cfg["DISP"]["size"] = 500
    prefixes = {v[:5] for v in run(cfg)["SERVER"]["IMSI"]}
    assert prefixes == {"41009"}


def test_encoded_imsi_round_trips_through_elect():
    cfg = copy.deepcopy(_BASE)
    cfg["DISP"]["imsi"] = "001010000000001"
    cfg["DISP"]["elect_check"] = True
    cfg["DISP"]["server_check"] = False
    encoded = run(cfg)["ELECT"]["IMSI"].tolist()
    assert [EncodingUtils.dec_imsi(v) for v in encoded] == [
        "001010000000001",
        "001010000000002",
        "001010000000003",
    ]


# ------------------------------------------------------------------ #
# Laser column assembly
# ------------------------------------------------------------------ #


def test_laser_positions_applied_in_numeric_key_order():
    cfg = copy.deepcopy(_BASE)
    cfg["DISP"]["server_check"] = False
    cfg["DISP"]["graph_check"] = True
    cfg["PARAMETERS"]["laser_variables"] = {
        "2": ["PIN1", "Normal", "0-3"],
        "0": ["ICCID", "Normal", "0-3"],
        "1": ["IMSI", "Normal", "0-5"],
    }
    assert list(run(cfg)["GRAPH"].columns) == ["ICCID", "IMSI", "PIN1"]


def test_more_than_ten_repetitions_of_one_column():
    # A hardcoded ceiling of 10 made this fail with "['ICCID10'] not in index".
    cfg = copy.deepcopy(_BASE)
    cfg["DISP"]["server_check"] = False
    cfg["DISP"]["graph_check"] = True
    cfg["PARAMETERS"]["laser_variables"] = {
        str(i): ["ICCID", "Normal", "0-3"] for i in range(12)
    }
    graph = run(cfg)["GRAPH"]
    assert len(graph.columns) == 12
    assert graph.iloc[0].nunique() == 1  # every position shows the same value
