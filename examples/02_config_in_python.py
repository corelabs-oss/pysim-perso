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
"""Build a configuration in Python instead of reading a settings file.

Useful when the parameters come from a database, a web request or a test
fixture rather than from disk. The dictionary is validated exactly as a file
would be, so a bad K4 length or an unknown column name still fails here.

Run:
    python examples/02_config_in_python.py
"""

import tempfile

from gsm_data_generator import (
    DataGenerationScript,
    json_loader_2_ConfigHolder,
)
from gsm_data_generator.error import DATAGENError


def build_config(output_dir: str, size: int) -> dict:
    return {
        "DISP": {
            "elect_data_sep": ",",
            "server_data_sep": ",",
            "graph_data_sep": ",",
            # K4 is the transport key Ki is encrypted under; 32 or 64 hex chars.
            "K4": "0000555500006666000077770000111100005555000066660000777700001111",
            "op": "00001111000022220000333300004444",
            "imsi": "410010000000001",
            "iccid": "8944000000000000001",
            "pin1": "1234",
            "puk1": "12345678",
            "pin2": "5678",
            "puk2": "87654321",
            "adm1": "AABBCCDD",
            "adm6": "11223344",
            "size": size,
            "prod_check": True,
            "elect_check": True,
            "graph_check": False,
            "server_check": True,
            # *_fix true  -> every card in the batch shares the configured value
            # *_fix false -> a fresh random value per card
            "pin1_fix": True,
            "puk1_fix": True,
            "pin2_fix": True,
            "puk2_fix": True,
            "adm1_fix": False,
            "adm6_fix": False,
        },
        "PATHS": {
            "FILE_NAME": "batch_from_python",
            "OUTPUT_FILES_DIR": output_dir,
            "OUTPUT_FILES_LASER_EXT": "laser",
        },
        "PARAMETERS": {
            "data_variables": ["IMSI", "ICCID", "KI", "OPC", "ACC", "PIN1", "PUK1"],
            "server_variables": ["IMSI", "EKI", "ICCID", "ACC"],
            "laser_variables": {},
        },
    }


def main() -> None:
    output_dir = tempfile.mkdtemp(prefix="gsm-python-config-")
    config = json_loader_2_ConfigHolder(build_config(output_dir, size=5))

    script = DataGenerationScript(config)
    script.json_to_global_params()
    result_dfs, _ = script.generate_all_data()

    # ELECT carries KI in the clear for the personalization line; SERVER carries
    # EKI instead, because the network side receives Ki under the transport key.
    print("ELECT columns :", list(result_dfs["ELECT"].columns))
    print("SERVER columns:", list(result_dfs["SERVER"].columns))
    print()
    print(result_dfs["SERVER"].head(3).to_string(index=False))
    print()

    # Validation is not advisory. An invalid K4 is rejected before any card is
    # produced, rather than yielding a batch that fails at personalization.
    broken = build_config(output_dir, size=5)
    broken["DISP"]["K4"] = "ABCD"
    try:
        json_loader_2_ConfigHolder(broken)
    except (DATAGENError, ValueError) as exc:
        first_line = str(exc).strip().splitlines()[0]
        print(f"rejected short K4 as expected: {first_line}")


if __name__ == "__main__":
    main()
