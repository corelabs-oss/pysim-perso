<!--- Licensed to the Apache Software Foundation (ASF) under one -->
<!--- or more contributor license agreements.  See the NOTICE file -->
<!--- distributed with this work for additional information -->
<!--- regarding copyright ownership.  The ASF licenses this file -->
<!--- to you under the Apache License, Version 2.0 (the -->
<!--- "License"); you may not use this file except in compliance -->
<!--- with the License.  You may obtain a copy of the License at -->

<!---   http://www.apache.org/licenses/LICENSE-2.0 -->

<!--- Unless required by applicable law or agreed to in writing, -->
<!--- software distributed under the License is distributed on an -->
<!--- "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY -->
<!--- KIND, either express or implied.  See the License for the -->
<!--- specific language governing permissions and limitations -->
<!--- under the License. -->


<table>
  <tr>
    <td><img src="https://raw.githubusercontent.com/hamzaqureshi5/gsm-data-generator-gui/ds0/src/resources/icon_without_text.png" width="128"/></td>
    <td style="vertical-align: middle; padding-left: 16px;">
      <h1>Open GSM Data Generation Stack</h1>
    </td>
  </tr>
</table>
[Documentation]() |
[Contributors](CONTRIBUTORS.md) |
[Community]() |
[Release Notes](NEWS.md)

GSM Data Generator is a library for generating and processing structured datasets for GSM, USIM, and eSIM systems. It is designed to bridge the gap between telecom operator requirements and developer productivity, offering flexible tools for data parsing, formatting, and export. The library provides an extensible framework to define operator-specific templates, process large-scale inputs, and generate outputs in standardized formats for downstream telecom systems.

License
-------
Licensed under the [Apache-2.0](LICENSE) license.

Quick Start
-----------

**1. Install**

```bash
pip install -e .
```

**2. Copy and edit the example config**

```bash
cp settings.example.json settings.json
```

Open `settings.json` and set at minimum: `imsi`, `iccid`, `K4`, `op`, and `size`.

**3. Generate SIM data**

```python
from gsm_data_generator import json_loader, DataGenerationScript

config = json_loader("settings.json")
script = DataGenerationScript(config)
script.json_to_global_params()

result_dfs, keys = script.generate_all_data()

elect_df = result_dfs["ELECT"]   # pandas DataFrame — one row per SIM
print(elect_df.head())
```

**4. Verify your install works end-to-end**

```bash
python verify.py
```

Configuration Reference
-----------------------

### DISP — generation parameters

| Field | Type | Description |
|---|---|---|
| `elect_data_sep` | string | Column separator for ELECT output (e.g. `","`) |
| `server_data_sep` | string | Column separator for SERVER output |
| `graph_data_sep` | string | Column separator for GRAPH output |
| `K4` | hex string (32–64 chars) | Transport key — used to encrypt Ki → eKI via AES-128 |
| `op` | hex string (exactly 32 chars) | Operator key — OPc = AES_Ki(OP) XOR OP |
| `imsi` | 15 digits | Starting IMSI; each SIM gets `imsi + row_index` |
| `iccid` | 18–19 digits | Starting ICCID; incremented per SIM |
| `pin1` / `pin2` | 4 digits | PIN value. Used as-is when `pin1_fix: true`; ignored when `false` (random generated) |
| `puk1` / `puk2` | 8 digits | PUK value. Same fixed-vs-random logic via `puk1_fix` |
| `adm1` / `adm6` | 8 chars | ADM codes. `adm1_fix: true` → fixed; `false` → random 8 digits per SIM |
| `size` | integer (1–1,000,000) | Number of SIM records to generate |
| `prod_check` | bool | Validate all parameters before generation (recommended: `true`) |
| `elect_check` | bool | Enable ELECT (personalization) output |
| `graph_check` | bool | Enable GRAPH (laser) output |
| `server_check` | bool | Enable SERVER output |
| `pin1_fix` / `puk1_fix` / `adm1_fix` … | bool | `true` = every SIM gets the fixed value above; `false` = unique random value per SIM |

### PATHS — output file locations

| Field | Description |
|---|---|
| `FILE_NAME` | Base name for output files (no extension) |
| `OUTPUT_FILES_DIR` | Directory where output files are written |
| `OUTPUT_FILES_LASER_EXT` | Suffix for laser/graph output filename |

### PARAMETERS — output column selection

| Field | Description |
|---|---|
| `data_variables` | Ordered list of columns in the ELECT output |
| `server_variables` | Ordered list of columns in the SERVER output |
| `laser_variables` | Dict mapping position index → `[column, type, "start-end"]` for GRAPH/laser output |

Valid column names for `data_variables` / `server_variables`:
`ICCID IMSI OP K4 PIN1 PUK1 PIN2 PUK2 KI EKI OPC ADM1 ADM6 ACC KIC1 KID1 KIK1 KIC2 KID2 KIK2 KIC3 KID3 KIK3`

`laser_variables` example: `"0": ["ICCID", "Normal", "0-18"]` — position 0 takes chars 0–18 of ICCID.

Features
--------
- Cryptographic SIM parameter generation: Ki, OPc, eKI, ACC, PIN/PUK, OTA keys
- Operator-configurable via a single JSON file
- Three output formats: ELECT (personalization), SERVER (provisioning), GRAPH (laser)
- Pydantic-validated config with clear error messages on bad input
- Thread-safe singleton state for use in GUI and pipeline contexts

Contribute
----------
Data Generation is an open-source project. Contributions are welcome — please open an issue or pull request on GitHub.

History
-------
Data Generation started as a research project for USIM/eSIM provisioning tooling and has gone through several rounds of redesign.

