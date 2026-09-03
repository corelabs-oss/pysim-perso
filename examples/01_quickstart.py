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
"""Generate one batch end to end, from a configuration file.

Run:
    python examples/01_quickstart.py
"""

import tempfile
from pathlib import Path

from pysim_perso import DataGenerationScript, json_loader

REPO_ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    config = json_loader(str(REPO_ROOT / "settings.example.json"))

    # The example config writes to a relative "output" directory. Point it at a
    # throwaway directory so this example leaves nothing behind; a real run
    # would keep a stable directory, because the issuance ledger lives there
    # and is what stops a batch being issued twice. See 05_issuance_ledger.py.
    config.PATHS.OUTPUT_FILES_DIR = tempfile.mkdtemp(prefix="gsm-quickstart-")

    script = DataGenerationScript(config)
    script.json_to_global_params()

    # Nothing is written yet: generate_all_data builds pandas frames in memory.
    result_dfs, keys = script.generate_all_data()

    print(f"batch size : {script.params.DATA_SIZE}")
    print(f"frames     : {', '.join(sorted(result_dfs))}")
    print(f"OP         : {keys['op']}")
    print()

    elect = result_dfs["ELECT"]
    print(f"ELECT frame: {len(elect)} rows x {len(elect.columns)} columns")
    print(elect[["ICCID", "IMSI", "KI", "OPC", "ACC"]].head().to_string(index=False))
    print()

    # write_outputs is the point at which the batch counts as issued.
    written = script.write_outputs(result_dfs)
    for output_type, path in sorted(written.items()):
        print(f"{output_type:<7} -> {path}")


if __name__ == "__main__":
    main()
