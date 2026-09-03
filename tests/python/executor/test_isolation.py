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
"""Each DataGenerationScript owns its own parameter state."""

import copy

import pytest

from pysim_perso.executor.script import DataGenerationScript
from pysim_perso.generator.generate import DataGenerator
from pysim_perso.globals.parameters import DataFrames, Parameters
from pysim_perso.parser.utils import json_loader_2_ConfigHolder

_BASE = {
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
        "size": 2,
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
        "server_variables": ["IMSI", "KI"],
        "data_variables": ["IMSI"],
        "laser_variables": {"0": ["ICCID", "Normal", "0-17"]},
    },
}


@pytest.fixture(autouse=True)
def reset_shared():
    DataFrames.reset_shared_instance()
    yield
    DataFrames.reset_shared_instance()


def _script(config, **kwargs):
    s = DataGenerationScript(json_loader_2_ConfigHolder(config), **kwargs)
    s.json_to_global_params()
    return s


# ------------------------------------------------------------------ #
# Cross-config contamination
# ------------------------------------------------------------------ #


def test_two_scripts_do_not_share_parameter_state():
    a = copy.deepcopy(_BASE)
    a["DISP"]["imsi"] = "111111111111111"
    b = copy.deepcopy(_BASE)
    b["DISP"]["imsi"] = "222222222222222"
    script_a, script_b = _script(a), _script(b)
    assert script_a.params.IMSI == "111111111111111"
    assert script_b.params.IMSI == "222222222222222"
    assert script_a.params is not script_b.params


def test_later_script_does_not_change_earlier_output():
    # Previously the last json_to_global_params() call in the process won,
    # so script_a generated script_b's IMSI range.
    a = copy.deepcopy(_BASE)
    a["DISP"]["imsi"] = "111111111111111"
    b = copy.deepcopy(_BASE)
    b["DISP"]["imsi"] = "222222222222222"
    script_a = _script(a)
    _script(b)  # loaded after script_a
    result, _ = script_a.generate_all_data()
    assert result["SERVER"]["IMSI"].tolist() == [
        "111111111111111",
        "111111111111112",
    ]


def test_script_does_not_publish_to_the_shared_instance():
    _script(copy.deepcopy(_BASE))
    assert Parameters.get_instance().IMSI == ""


def test_explicitly_shared_params_are_honoured():
    shared = Parameters()
    first = _script(copy.deepcopy(_BASE), params=shared)
    second = _script(copy.deepcopy(_BASE), params=shared)
    assert first.params is shared and second.params is shared


def test_dataframes_role_is_backed_by_the_same_object():
    script = _script(copy.deepcopy(_BASE))
    assert script.dataframes is script.params


# ------------------------------------------------------------------ #
# Shared-instance accessors
# ------------------------------------------------------------------ #


def test_dataframes_before_parameters_does_not_raise():
    # Creating DataFrames first used to poison Parameters.get_instance()
    # with "DataFrames is a singleton".
    frames = DataFrames.get_instance()
    params = Parameters.get_instance()
    assert frames is params
    assert isinstance(frames, Parameters)


def test_parameters_before_dataframes_gives_the_same_object():
    params = Parameters.get_instance()
    assert DataFrames.get_instance() is params


def test_direct_construction_is_allowed():
    assert Parameters() is not Parameters()
    assert DataFrames() is not DataFrames()


def test_direct_construction_does_not_affect_shared_instance():
    shared = Parameters.get_instance()
    Parameters()
    assert Parameters.get_instance() is shared


def test_reset_shared_instance_creates_a_fresh_one():
    first = Parameters.get_instance()
    first.IMSI = "999999999999999"
    DataFrames.reset_shared_instance()
    assert Parameters.get_instance().IMSI == ""


# ------------------------------------------------------------------ #
# Generator injection
# ------------------------------------------------------------------ #


class _FixedGenerator:
    """Deterministic stand-in; never acceptable for real cards."""

    def generate_ki(self):
        return "0" * 32

    def generate_otas(self):
        return "1" * 32

    def generate_4_digit(self):
        return "4321"

    def generate_8_digit(self):
        return "87654321"


def test_generator_can_be_injected():
    script = _script(copy.deepcopy(_BASE), data_generator=_FixedGenerator())
    result, _ = script.generate_all_data()
    assert result["SERVER"]["KI"].tolist() == ["0" * 32] * 2


def test_default_generator_is_the_secrets_backed_one():
    script = _script(copy.deepcopy(_BASE))
    assert isinstance(script.data_generator, DataGenerator)


def test_default_generator_still_produces_unique_keys():
    config = copy.deepcopy(_BASE)
    config["DISP"]["size"] = 200
    result, _ = _script(config).generate_all_data()
    assert result["SERVER"]["KI"].nunique() == 200
