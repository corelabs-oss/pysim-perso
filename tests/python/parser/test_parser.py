# test_config.py
import json
import pytest
from pysim_perso.parser.utils import (
    DISP,
    PATHS,
    PARAMETERS,
    ConfigData,
    ConfigHolder,
    json_loader,
    json_loader_2_ConfigHolder,
    gui_loader,
)


@pytest.fixture
def valid_config_dict():
    return {
        "DISP": {
            "elect_data_sep": ",",
            "server_data_sep": ";",
            "graph_data_sep": "|",
            "K4": "A" * 64,
            "op": "B" * 32,
            "imsi": "123456789012345",
            "iccid": "1234567890123456789",
            "pin1": "1234",
            "puk1": "87654321",
            "pin2": "4321",
            "puk2": "12345678",
            "adm1": "11111111",
            "adm6": "22222222",
            "size": 5000,
            "prod_check": True,
            "elect_check": False,
            "graph_check": True,
            "server_check": True,
            "pin1_fix": False,
            "puk1_fix": False,
            "pin2_fix": True,
            "puk2_fix": False,
            "adm1_fix": False,
            "adm6_fix": True,
        },
        "PATHS": {
            "FILE_NAME": "output.txt",
            "OUTPUT_FILES_DIR": "/tmp",
            "OUTPUT_FILES_LASER_EXT": ".laser",
        },
        "PARAMETERS": {
            "server_variables": ["IMSI", "ICCID"],
            "data_variables": ["IMSI", "ICCID"],
            "laser_variables": {"0": ["ICCID", "Normal", "0-18"]},
        },
    }


def test_disp_validation(valid_config_dict):
    disp = DISP(**valid_config_dict["DISP"])
    assert disp.imsi == "123456789012345"
    assert disp.iccid.startswith("1234")

    # length violation
    with pytest.raises(Exception):
        DISP(**{**valid_config_dict["DISP"], "imsi": "123"})


def test_paths_validation(valid_config_dict):
    paths = PATHS(**valid_config_dict["PATHS"])
    assert paths.FILE_NAME == "output.txt"

    # missing required
    bad_paths = valid_config_dict["PATHS"].copy()
    bad_paths.pop("FILE_NAME")
    with pytest.raises(Exception):
        PATHS(**bad_paths)


def test_parameters_validation(valid_config_dict):
    params = PARAMETERS(**valid_config_dict["PARAMETERS"])
    assert "IMSI" in params.server_variables
    assert isinstance(params.laser_variables, dict)


def test_configdata_and_holder(valid_config_dict):
    cfg = ConfigData(**valid_config_dict)
    holder = ConfigHolder.from_config(cfg)
    assert holder.DISP.imsi == "123456789012345"
    assert holder.PATHS.FILE_NAME == "output.txt"
    assert isinstance(holder.PARAMETERS.laser_variables, dict)


def test_json_loader(tmp_path, valid_config_dict):
    file_path = tmp_path / "config.json"
    file_path.write_text(json.dumps(valid_config_dict))

    holder = json_loader(str(file_path))
    assert isinstance(holder, ConfigHolder)
    assert holder.DISP.op == "B" * 32


def test_json_loader1_dict(valid_config_dict):
    holder = json_loader_2_ConfigHolder(valid_config_dict)
    assert holder.DISP.pin1 == "1234"


def test_json_loader1_jsonstring(valid_config_dict):
    json_str = json.dumps(valid_config_dict)
    holder = json_loader_2_ConfigHolder(json_str)
    assert holder.DISP.puk1 == "87654321"


def test_json_loader1_invalid():
    with pytest.raises(ValueError):
        json_loader_2_ConfigHolder(123)  # type: ignore # not dict or str
    with pytest.raises(ValueError):
        json_loader_2_ConfigHolder("{bad json}")  # invalid JSON string


def test_gui_loader(valid_config_dict):
    holder = gui_loader(valid_config_dict)
    assert isinstance(holder, ConfigHolder)
    assert holder.PATHS.OUTPUT_FILES_DIR == "/tmp"
