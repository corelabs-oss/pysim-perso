from gsm_data_generator.executor import DataGenerationScript
from gsm_data_generator.parser import json_loader_2_ConfigHolder, json_loader
from gsm_data_generator.parser.utils import ConfigHolder
from gsm_data_generator.utils import list_2_dict, dict_2_list
import json
from gsm_data_generator.globals import Parameters

import pytest
import json
from gsm_data_generator.executor import DataGenerationScript
from gsm_data_generator.parser import json_loader_2_ConfigHolder
from gsm_data_generator.globals import Parameters

p = Parameters.get_instance()

p.ELECT_SEP = ","
p.GRAPH_SEP = ","
p.SERVR_SEP = ","

p.K4 = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
p.OP = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
p.IMSI = "111111111121111"
p.ICCID = "111111111121221111"
p.PIN1 = "1111"
p.PUK1 = "11111111"
p.PIN2 = "1111"
p.PUK2 = "11111111"
p.ADM1 = "11111111"
p.ADM6 = "11111111"
p.ACC = "1111"
p.DATA_SIZE = "5"
# p.PRODUCTION_CHECK = True
p.GRAPH_CHECK = True
p.ELECT_CHECK = True
p.SERVER_CHECK = True
p.PIN1_RAND = False
p.PIN2_RAND = False
p.PUK1_RAND = False
p.PUK2_RAND = False
p.ADM1_RAND = False
p.ADM6_RAND = False

# p.ELECT_SEP = ","
# p.set_GRAPH_SEP(",")
# p.set_SERVER_SEP(",")

# p.set_K4("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
# p.set_OP("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
# p.set_IMSI("111111111121111")
# p.set_ICCID("111111111121221111")
# p.set_PIN1("1111")
# p.set_PUK1("11111111")
# p.set_PIN2("1111")
# p.set_PUK2("11111111")
# p.set_ADM1("11111111")
# p.set_ADM6("11111111")
# p.set_ACC("1111")
# p.set_DATA_SIZE("5")
# # p.set_PRODUCTION_CHECK(True)
# p.set_GRAPH_CHECK(True)
# p.set_ELECT_CHECK(True)
# p.set_SERVER_CHECK(True)
# p.set_PIN1_RAND(False)
# p.set_PIN2_RAND(False)

# p.set_PUK1_RAND(False)
# p.set_PUK2_RAND(False)
# p.set_ADM1_RAND(False)
# p.set_ADM6_RAND(False)

p.ELECT_DF = list_2_dict(
    [
        "IMSI",
        "ICCID",
        "PIN1",
        "PUK1",
        "PIN2",
        "PUK2",
        "ADM1",
        "ADM6",
        "KI",
        "OPC",
        "ACC",
        "KIC1",
        "KID1",
        "KIK1",
        "KIC2",
        "KID2",
        "KIK2",
        "KIC3",
        "KID3",
        "KIK3",
    ]
)


p.SERVER_DICT = list_2_dict(
    [
        "IMSI",
        "EKI",
        "ICCID",
        "PIN1",
        "PUK1",
        "PIN2",
        "PUK2",
        "ADM1",
        "ADM6",
        "ACC",
        "KIC1",
        "KID1",
        "KIK1",
        "KIC2",
        "KID2",
        "KIK2",
        "KIC3",
        "KID3",
        "KIK3",
    ]
)

p.GRAPH_DICT = {
    "0": ["ICCID", "Normal", "0-20"],
    "1": ["ICCID", "Normal", "0-20"],
    "2": ["ICCID", "Normal", "0-3"],
    "3": ["ICCID", "Normal", "4-7"],
    "4": ["ICCID", "Normal", "8-11"],
    "5": ["ICCID", "Normal", "12-15"],
    "6": ["ICCID", "Normal", "16-20"],
    "7": ["PIN1", "Normal", "0-3"],
    "8": ["PUK1", "Normal", "0-7"],
    "9": ["PIN2", "Normal", "0-3"],
    "10": ["PUK2", "Normal", "0-7"],
    "11": ["IMSI", "Normal", "0-5"],
    "12": ["IMSI", "Normal", "6-15"],
}


def global_params_to_json():
    param_dict = {
        "DISP": {
            "elect_data_sep": ".",
            "server_data_sep": ".",
            "graph_data_sep": ".",
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
            "acc": "1111",
            "size": "11",
            "prod_check": 1,
            "elect_check": 1,
            "graph_check": 1,
            "server_check": 1,
            "pin1_fix": 1,
            "puk1_fix": 1,
            "pin2_fix": 1,
            "puk2_fix": 1,
            "adm1_fix": 1,
            "adm6_fix": 1,
        },
        "PATHS": {
            "FILE_NAME": "get_file_name",
            "OUTPUT_FILES_DIR": "output_files1",
            "OUTPUT_FILES_LASER_EXT": "laser_extracted",
        },
        "PARAMETERS": {
            "server_variables": [
                "IMSI",
                "EKI",
                "ICCID",
                "PIN1",
                "PUK1",
                "PIN2",
                "PUK2",
                "ADM1",
                "ADM6",
                "ACC",
                "KIC1",
                "KID1",
                "KIK1",
                "KIC2",
                "KID2",
                "KIK2",
                "KIC3",
                "KID3",
                "KIK3",
            ],
            "data_variables": [
                "IMSI",
                "ICCID",
                "PIN1",
                "PUK1",
                "PIN2",
                "PUK2",
                "ADM1",
                "ADM6",
                "KI",
                "OPC",
                "ACC",
                "KIC1",
                "KID1",
                "KIK1",
                "KIC2",
                "KID2",
                "KIK2",
                "KIC3",
                "KID3",
                "KIK3",
            ],
            "laser_variables": {
                "0": ["ICCID", "Normal", "0-20"],
                "1": ["ICCID", "Normal", "0-20"],
                "2": ["ICCID", "Normal", "0-3"],
                "3": ["ICCID", "Normal", "4-7"],
                "4": ["ICCID", "Normal", "8-11"],
                "5": ["ICCID", "Normal", "12-15"],
                "6": ["ICCID", "Normal", "16-20"],
                "7": ["PIN1", "Normal", "0-3"],
                "8": ["PUK1", "Normal", "0-7"],
                "9": ["PIN2", "Normal", "0-3"],
                "10": ["PUK2", "Normal", "0-7"],
                "11": ["IMSI", "Normal", "0-5"],
                "12": ["IMSI", "Normal", "6-15"],
            },
        },
    }

    return param_dict


@pytest.fixture
def params_dict():
    """Fixture to provide global params dict."""
    return global_params_to_json()


def test_json_loader1_returns_dict(params_dict):
    js = json_loader_2_ConfigHolder(params_dict)
    assert isinstance(js, ConfigHolder), "json_loader1 should return a ConfigHolder"
    # assert "DISP" in js.DISP.adm1
    # assert "PARAMETERS" in js.PARAMETERS.data_variables
    # assert "PATHS" in js.PATHS.OUTPUT_FILES_DIR


def test_data_generation_script_runs(params_dict, tmp_path):
    js = json_loader_2_ConfigHolder(params_dict)

    # Override output dir to temp folder so tests don't pollute real dirs
    # js["PATHS"]["OUTPUT_FILES_DIR"] = str(tmp_path / "output_files")
    # js["PATHS"]["OUTPUT_FILES_LASER_EXT"] = str(tmp_path / "laser_extracted")

    script = DataGenerationScript(js)

    # Step 1: apply JSON params to global Parameters singleton
    script.json_to_global_params()
    p = Parameters.get_instance()

    # sanity checks
    assert p.IMSI == "111111111121111"
    assert p.PIN1 == "1111"

    # Step 2: run data generation (should not raise)
    script.generate_all_data()

    # Verify expected outputs
    # out_dir = tmp_path / "output_files"
    # assert out_dir.exists(), "Output directory should be created"
    # You can also check specific files if you know what gets generated:
    # assert any(out_dir.iterdir()), "Expected at least one file in output dir"


# def test_script():
#     t = global_params_to_json()
#     js = json_loader1(t)
#     #js = json_loader("settings.json")

#     s = DataGenerationScript(js)
#     s.json_to_global_params()
#     s.generate_all_data()
