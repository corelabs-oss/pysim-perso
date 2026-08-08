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
"""Show the issuance ledger refusing to issue the same identifiers twice.

Running one configuration twice yields identical ICCIDs and IMSIs but fresh,
unrelated Ki values. The two card populations would collide in the HLR, which
keys the subscriber by identifier. The ledger turns that into an error at
write time rather than a field failure.

Run:
    python examples/05_issuance_ledger.py
"""

import tempfile

from gsm_data_generator import DataGenerationScript, json_loader_2_ConfigHolder
from gsm_data_generator.error import IssuanceOverlapError

BASE = {
    "DISP": {
        "elect_data_sep": ",",
        "server_data_sep": ",",
        "graph_data_sep": ",",
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
        "size": 10,
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
        "FILE_NAME": "batch",
        "OUTPUT_FILES_DIR": "",
        "OUTPUT_FILES_LASER_EXT": "laser",
    },
    "PARAMETERS": {
        "data_variables": ["IMSI", "ICCID", "KI", "OPC", "ACC"],
        "server_variables": ["IMSI", "EKI", "ICCID"],
        "laser_variables": {},
    },
}


def run_batch(output_dir: str, file_name: str, iccid: str, imsi: str) -> dict:
    """Generate and write one batch, returning the paths written."""
    config_dict = {
        "DISP": {**BASE["DISP"], "iccid": iccid, "imsi": imsi},
        "PATHS": {
            **BASE["PATHS"],
            "OUTPUT_FILES_DIR": output_dir,
            "FILE_NAME": file_name,
        },
        "PARAMETERS": BASE["PARAMETERS"],
    }
    script = DataGenerationScript(json_loader_2_ConfigHolder(config_dict))
    script.json_to_global_params()
    result_dfs, _ = script.generate_all_data()
    return script.write_outputs(result_dfs)


def main() -> None:
    output_dir = tempfile.mkdtemp(prefix="gsm-ledger-")
    print(f"output directory: {output_dir}\n")

    # First batch: ICCIDs ...001 through ...010.
    run_batch(output_dir, "batch_001", "8944000000000000001", "410010000000001")
    print("batch 1 written")

    # Same starting identifiers again. Generation still succeeds — the ledger is
    # only consulted at write time, because that is when cards become real.
    try:
        run_batch(output_dir, "batch_002", "8944000000000000001", "410010000000001")
    except IssuanceOverlapError as exc:
        print("batch 2 refused:")
        print(f"  {exc}")
    else:
        raise AssertionError("expected the ledger to refuse this batch")
    print()

    # Advance past the issued range and the write succeeds.
    run_batch(output_dir, "batch_003", "8944000000000000011", "410010000000011")
    print("batch 3 written after advancing the starting identifiers\n")

    # The ledger is a plain JSON file beside the output.
    script = DataGenerationScript(
        json_loader_2_ConfigHolder(
            {
                "DISP": BASE["DISP"],
                "PATHS": {**BASE["PATHS"], "OUTPUT_FILES_DIR": output_dir},
                "PARAMETERS": BASE["PARAMETERS"],
            }
        )
    )
    print(f"ledger file: {script.ledger.path}")
    for record in script.ledger.records():
        print(
            f"  batch {record['batch']}: "
            f"ICCID {record['iccid_start']}-{record['iccid_end']} "
            f"({record['size']} cards)"
        )


if __name__ == "__main__":
    main()
