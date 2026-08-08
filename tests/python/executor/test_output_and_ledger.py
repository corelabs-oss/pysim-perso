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
"""File output and the issuance ledger that guards against re-issuing."""

import copy
import json

import pandas as pd
import pytest

from gsm_data_generator.error import IssuanceOverlapError
from gsm_data_generator.executor.script import DataGenerationScript
from gsm_data_generator.globals.parameters import DataFrames
from gsm_data_generator.issuance import LEDGER_FILENAME, IssuanceLedger
from gsm_data_generator.parser.utils import json_loader_2_ConfigHolder
from gsm_data_generator.writer import OutputWriter

_BASE = {
    "DISP": {
        "elect_data_sep": ",",
        "server_data_sep": ";",
        "graph_data_sep": "|",
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
        "graph_check": True,
        "server_check": True,
        "pin1_fix": True,
        "puk1_fix": True,
        "pin2_fix": True,
        "puk2_fix": True,
        "adm1_fix": False,
        "adm6_fix": False,
    },
    "PATHS": {
        "FILE_NAME": "BATCH_001",
        "OUTPUT_FILES_DIR": "out",
        "OUTPUT_FILES_LASER_EXT": "laser_extracted",
    },
    "PARAMETERS": {
        "server_variables": ["IMSI", "ICCID"],
        "data_variables": ["IMSI", "ICCID"],
        # Two positions so the separator is actually exercised in the output.
        "laser_variables": {
            "0": ["ICCID", "Normal", "0-17"],
            "1": ["IMSI", "Normal", "0-14"],
        },
    },
}


@pytest.fixture(autouse=True)
def reset_shared():
    DataFrames.reset_shared_instance()
    yield
    DataFrames.reset_shared_instance()


@pytest.fixture
def config(tmp_path):
    cfg = copy.deepcopy(_BASE)
    cfg["PATHS"]["OUTPUT_FILES_DIR"] = str(tmp_path)
    return cfg


def _script(config):
    s = DataGenerationScript(json_loader_2_ConfigHolder(config))
    s.json_to_global_params()
    return s


# ------------------------------------------------------------------ #
# OutputWriter
# ------------------------------------------------------------------ #


def test_writes_one_file_per_enabled_output(config, tmp_path):
    script = _script(config)
    written = script.write_outputs(script.generate_all_data()[0])
    assert set(written) == {"ELECT", "GRAPH", "SERVER"}
    for path in written.values():
        assert path.exists()


def test_file_names_follow_the_configured_base_name(config, tmp_path):
    script = _script(config)
    written = script.write_outputs(script.generate_all_data()[0])
    assert written["ELECT"].name == "BATCH_001.txt"
    assert written["SERVER"].name == "BATCH_001_server.txt"
    assert written["GRAPH"].name == "BATCH_001_laser_extracted.txt"


def test_each_output_uses_its_configured_separator(config):
    script = _script(config)
    written = script.write_outputs(script.generate_all_data()[0])
    assert "," in written["ELECT"].read_text().splitlines()[0]
    assert ";" in written["SERVER"].read_text().splitlines()[0]
    assert "|" in written["GRAPH"].read_text().splitlines()[0]


def test_row_count_matches_size_plus_header(config):
    script = _script(config)
    written = script.write_outputs(script.generate_all_data()[0])
    assert len(written["SERVER"].read_text().splitlines()) == 4


def test_header_can_be_suppressed(config):
    script = _script(config)
    written = script.write_outputs(script.generate_all_data()[0], include_header=False)
    assert len(written["SERVER"].read_text().splitlines()) == 3


def test_output_directory_is_created(tmp_path):
    cfg = copy.deepcopy(_BASE)
    target = tmp_path / "does" / "not" / "exist"
    cfg["PATHS"]["OUTPUT_FILES_DIR"] = str(target)
    script = _script(cfg)
    script.write_outputs(script.generate_all_data()[0])
    assert target.is_dir()


def test_writer_supports_multi_character_separators(tmp_path):
    writer = OutputWriter(tmp_path, "x", separators={"ELECT": "||"})
    written = writer.write({"ELECT": pd.DataFrame({"A": ["1"], "B": ["2"]})})
    assert written["ELECT"].read_text().splitlines()[1] == "1||2"


def test_writer_rejects_unknown_output_type(tmp_path):
    with pytest.raises(ValueError, match="Unknown output type"):
        OutputWriter(tmp_path, "x").path_for("NOPE")


# ------------------------------------------------------------------ #
# IssuanceLedger
# ------------------------------------------------------------------ #


def test_ledger_is_written_beside_the_output(config, tmp_path):
    script = _script(config)
    script.write_outputs(script.generate_all_data()[0])
    ledger_file = tmp_path / LEDGER_FILENAME
    assert ledger_file.exists()
    records = json.loads(ledger_file.read_text())
    assert len(records) == 1
    assert records[0]["size"] == 3


def test_reissuing_the_same_config_is_refused(config):
    first = _script(config)
    first.write_outputs(first.generate_all_data()[0])

    second = _script(config)
    with pytest.raises(IssuanceOverlapError, match="overlaps batch 1"):
        second.write_outputs(second.generate_all_data()[0])


def test_partially_overlapping_range_is_refused(config):
    first = _script(config)
    first.write_outputs(first.generate_all_data()[0])

    shifted = copy.deepcopy(config)
    shifted["DISP"]["iccid"] = "111111111121221112"  # overlaps by two
    shifted["DISP"]["imsi"] = "111111111121112"
    second = _script(shifted)
    with pytest.raises(IssuanceOverlapError):
        second.write_outputs(second.generate_all_data()[0])


def test_non_overlapping_range_is_allowed(config, tmp_path):
    first = _script(config)
    first.write_outputs(first.generate_all_data()[0])

    advanced = copy.deepcopy(config)
    advanced["DISP"]["iccid"] = "111111111121221200"
    advanced["DISP"]["imsi"] = "111111111121200"
    second = _script(advanced)
    second.write_outputs(second.generate_all_data()[0])

    assert len(IssuanceLedger(tmp_path).records()) == 2


def test_issuance_check_can_be_disabled(config):
    first = _script(config)
    first.write_outputs(first.generate_all_data()[0])
    second = _script(config)
    second.write_outputs(second.generate_all_data()[0], check_issuance=False)


def test_generating_without_writing_does_not_record(config, tmp_path):
    # A batch counts as issued when it is written, not when it is generated,
    # so in-memory use never consumes an identifier range.
    script = _script(config)
    script.generate_all_data()
    script.generate_all_data()
    assert not (tmp_path / LEDGER_FILENAME).exists()


def test_corrupt_ledger_refuses_to_issue(config, tmp_path):
    (tmp_path / LEDGER_FILENAME).write_text("{not valid json")
    script = _script(config)
    with pytest.raises(IssuanceOverlapError, match="corrupt"):
        script.write_outputs(script.generate_all_data()[0])


def test_issued_ranges_reports_the_configured_span(config):
    script = _script(config)
    ranges = script.issued_ranges()
    assert ranges["iccid_start"] == "111111111121221111"
    assert ranges["iccid_end"] == "111111111121221113"
    assert ranges["imsi_start"] == "111111111121111"
    assert ranges["imsi_end"] == "111111111121113"
    assert ranges["size"] == 3


def test_ledger_records_are_numbered_in_order(tmp_path):
    ledger = IssuanceLedger(tmp_path)
    ledger.record("100", "109", "200", "209", 10)
    ledger.record("110", "119", "210", "219", 10)
    assert [r["batch"] for r in ledger.records()] == [1, 2]


def test_empty_ledger_reads_as_no_records(tmp_path):
    assert IssuanceLedger(tmp_path).records() == []
