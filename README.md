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

[![CI](https://github.com/hamzaqureshi5/gsm-data-generation_lib/actions/workflows/ci.yml/badge.svg)](https://github.com/hamzaqureshi5/gsm-data-generation_lib/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache--2.0-green)](LICENSE)

[Documentation]() |
[Contributors](CONTRIBUTORS.md) |
[Community]() |
[Release Notes](NEWS.md)

GSM Data Generator is a library for generating and processing structured datasets for GSM, USIM, and eSIM systems. It is designed to bridge the gap between telecom operator requirements and developer productivity, offering flexible tools for data parsing, formatting, and export. The library provides an extensible framework to define operator-specific templates, process large-scale inputs, and generate outputs in standardized formats for downstream telecom systems.

License
-------
Licensed under the [Apache-2.0](LICENSE) license.

Requirements
------------
Python 3.10 or newer. Runtime dependencies (`pandas`, `pydantic`,
`pycryptodome`, `numpy`) are installed automatically.

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

# Write the files and record the batch as issued
written = script.write_outputs(result_dfs)
print(written["ELECT"])          # <OUTPUT_FILES_DIR>/<FILE_NAME>.txt
```

Each `DataGenerationScript` owns its own parameter state, so several
configurations can be generated in one process without interfering. Read a
run's state through `script.params`; `Parameters.get_instance()` still returns
a process-wide instance but is no longer where a script keeps its state.

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
| `K4` | hex string, exactly **32, 48 or 64** chars | Transport key — used to encrypt Ki → eKI. The length selects the AES variant: 32 → AES-128, 48 → AES-192, 64 → AES-256. Other lengths are rejected at load time. |
| `op` | hex string (exactly 32 chars) | Operator key — OPc = AES_Ki(OP) XOR OP |
| `imsi` | exactly 15 digits | Starting IMSI. Only the MSIN portion is incremented — see [Identifier sequencing](#identifier-sequencing) |
| `iccid` | 18–19 digits | Starting ICCID (**without** the Luhn check digit — it is computed and appended during encoding); incremented per SIM |
| `pin1` / `pin2` | 4 digits | PIN value. Used as-is when `pin1_fix: true`; ignored when `false` (random generated) |
| `puk1` / `puk2` | 8 digits | PUK value. Same fixed-vs-random logic via `puk1_fix` |
| `adm1` / `adm6` | 8 printable ASCII chars | ADM codes. `adm1_fix: true` → fixed; `false` → random 8 digits per SIM |
| `size` | integer (1–1,000,000) | Number of SIM records to generate |
| `prod_check` | bool | Validate all parameters before generation (recommended: `true`). Raises `ConfigValidationError` listing every failing parameter. |
| `elect_check` | bool | Enable ELECT (personalization) output |
| `graph_check` | bool | Enable GRAPH (laser) output |
| `server_check` | bool | Enable SERVER output |
| `pin1_fix` / `puk1_fix` / `adm1_fix` … | bool | `true` = every SIM gets the fixed value above; `false` = unique random value per SIM |

All string fields are character-set checked at load time: identifiers must be
numeric, key material must be hexadecimal. Invalid values raise a Pydantic
`ValidationError` naming the offending field instead of failing later inside
the generation pipeline.

### Identifier sequencing

`imsi` and `iccid` are sequenced as fixed-width digit strings, not integers:

- **Leading zeros are preserved.** A test-network IMSI such as
  `001010000000001` stays 15 digits across the batch.
- **The IMSI prefix is protected.** An IMSI is MCC (3 digits) + MNC (2 or 3) +
  MSIN, so only the trailing 10 digits are incremented. A batch that would
  carry into the first 5 digits is rejected rather than silently reassigning
  the cards to a different operator — `410099999999998` with `size: 4` raises
  instead of rolling over to `410100000000000`.
- **ICCID is width-checked.** The whole value increments, but a batch that
  would grow the ICCID past its configured length is rejected.

> **Note:** the 5-digit protected prefix is a conservative bound that holds
> under every numbering plan. Where the MNC is 3 digits (the North American
> Numbering Plan) its final digit sits inside the incremented range and is not
> covered; keep such batches well clear of the MSIN boundary.

### PATHS — output file locations

| Field | Description |
|---|---|
| `FILE_NAME` | Base name for output files (no extension) |
| `OUTPUT_FILES_DIR` | Directory where output files and the issuance ledger are written; created if missing |
| `OUTPUT_FILES_LASER_EXT` | Suffix for laser/graph output filename |

`script.write_outputs(result_dfs)` writes one separator-delimited text file per
enabled output:

| Output | File |
|---|---|
| ELECT | `<FILE_NAME>.txt` |
| SERVER | `<FILE_NAME>_server.txt` |
| GRAPH | `<FILE_NAME>_<OUTPUT_FILES_LASER_EXT>.txt` |

### Issuance ledger

Re-running a configuration produces the **same** ICCID and IMSI sequences but
**fresh** Ki values. Two cards would then carry the same ICCID with different
keys and neither could be provisioned reliably.

`write_outputs` therefore records each batch in `.issuance_ledger.json` inside
`OUTPUT_FILES_DIR` and refuses a batch that overlaps one already issued:

```
IssuanceOverlapError: ICCID range 8991…000-8991…009 overlaps batch 1
(8991…000-8991…009, issued 2026-08-08T09:14:22+00:00). Re-issuing would
produce duplicate ICCIDs with different Ki values.
```

Advance the starting `iccid`/`imsi` to continue, or pass
`write_outputs(..., check_issuance=False)` to override deliberately. A batch
counts as issued when it is **written**, so generating frames in memory never
consumes a range.

### PARAMETERS — output column selection

| Field | Description |
|---|---|
| `data_variables` | Ordered list of columns in the ELECT output |
| `server_variables` | Ordered list of columns in the SERVER output |
| `laser_variables` | Dict mapping position index → `[column, type, "start-end"]` for GRAPH/laser output |

Valid column names for `data_variables` / `server_variables` / `laser_variables`:
`ICCID IMSI OP K4 PIN1 PUK1 PIN2 PUK2 KI EKI OPC ADM1 ADM6 ACC KIC1 KID1 KIK1 KIC2 KID2 KIK2 KIC3 KID3 KIK3`

Names are case-sensitive and validated at load time; an unknown column is
rejected with the list of valid names.

`laser_variables` example: `"0": ["ICCID", "Normal", "0-18"]` — position 0 takes chars 0–18 of ICCID.

Each entry must be exactly `[column, type, range]`, where:

- the **key** is the laser print position and must be a non-negative integer
  string (`"0"`, `"1"`, …). Entries are applied in ascending numeric key order,
  independent of the order they appear in the JSON file, and `"10"` correctly
  follows `"9"`.
- the **range** must be `"<start>-<end>"` with `start <= end`. A reversed range
  (`"5-3"`) or an unparseable one (`"garbage"`) is rejected — previously these
  silently produced an empty field or the whole value respectively.

Features
--------
- Cryptographic SIM parameter generation: Ki, OPc, eKI, ACC, PIN/PUK, OTA keys
- Operator-configurable via a single JSON file
- Three output formats: ELECT (personalization), SERVER (provisioning), GRAPH (laser)
- Pydantic-validated config, rejecting malformed values at load time with the
  offending field named
- Structure-preserving identifier sequencing that refuses to carry into an
  operator prefix
- Issuance ledger that prevents the same ICCID range being issued twice
- Per-run isolated state, so multiple configurations can be generated
  concurrently in one process

### Opt-in global behaviour

Importing the library no longer replaces `sys.excepthook`. Applications that
want the previous behaviour — suppressed backtraces for `DiagnosticError`
unless `DATAGEN_BACKTRACE=1`, and termination of active multiprocessing
children on an unhandled exception — should call it explicitly:

```python
from gsm_data_generator import install_excepthook
install_excepthook()
```

Development
-----------

```bash
# Editable install with the test tooling
pip install -e .
pip install pytest pytest-cov

# Run the suite (the invocation CI uses)
pytest --maxfail=1 --disable-warnings -v

# A single module
pytest tests/python/algorithm/test_encrypt.py -v

# Coverage
pytest --cov=gsm_data_generator --cov-report=term-missing
```

Formatting and typing are enforced in CI, so check them before pushing:

```bash
pip install black mypy pandas-stubs
black gsm_data_generator/ tests/python/ verify.py setup.py
mypy gsm_data_generator/
```

`pandas-stubs` is required for `mypy`: `mypy.ini` sets
`ignore_missing_imports = False`, so an unstubbed `pandas` is a hard error.

To build and check the distributions locally:

```bash
pip install build twine
python -m build
twine check dist/*
```

### Continuous integration

[`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs on every pull
request, on pushes to `main`, and weekly — dependencies are unpinned, so the
scheduled run surfaces upstream breakage without waiting for a PR.

| Job | Checks |
|---|---|
| `format` | `black --check` |
| `typecheck` | `mypy` with `pandas-stubs` |
| `test` | Python 3.10–3.13 on Ubuntu, plus 3.11 on Windows and macOS; `pip check`, the test suite with a coverage floor, and `verify.py` |
| `package` | Builds the sdist and wheel, validates metadata, installs the wheel into a clean environment and smoke-tests it |
| `ci-ok` | Aggregate gate — use this single check for branch protection |

Contribute
----------
Data Generation is an open-source project. Contributions are welcome — please open an issue or pull request on GitHub.

History
-------
Data Generation started as a research project for USIM/eSIM provisioning tooling and has gone through several rounds of redesign.

