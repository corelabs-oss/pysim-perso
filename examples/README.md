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

# Examples

Runnable scripts covering the library's public API. Each is self-contained and
writes only to a temporary directory, so they can be run in any order and leave
nothing behind.

```bash
pip install -e .
python examples/01_quickstart.py
```

| Script | Shows |
|---|---|
| [`01_quickstart.py`](01_quickstart.py) | Load a settings file, generate a batch, inspect the frame, write the output files |
| [`02_config_in_python.py`](02_config_in_python.py) | Build and validate a configuration from a dict instead of a file |
| [`03_key_derivation.py`](03_key_derivation.py) | Derive OPc, EKI and ACC directly; verify the TS 35.206 test vector |
| [`04_encoding.py`](04_encoding.py) | Encode and decode `EF_IMSI`, `EF_ICCID` and PINs; compute an E.118 check digit |
| [`05_issuance_ledger.py`](05_issuance_ledger.py) | Watch the ledger refuse to issue the same identifiers twice |
| [`06_reproducible_batch.py`](06_reproducible_batch.py) | Inject a seeded generator for deterministic tests |

## Two things worth knowing before you adapt these

**Generating is not issuing.** `generate_all_data()` builds pandas frames in
memory and touches nothing on disk. The batch counts as issued only when
`write_outputs()` runs, which is where the issuance ledger is consulted and
updated. That split is deliberate: you can generate freely, and the safety
check applies at the moment cards become real.

**The output directory is stateful.** The ledger lives in
`PATHS.OUTPUT_FILES_DIR`, so a real deployment points that at a stable location
and keeps it. These examples use throwaway directories, which means the
duplicate-issuance protection resets on every run — convenient for a demo,
wrong for production.

## A note on the seeded generator

`06_reproducible_batch.py` injects a PRNG so tests can assert on exact key
values. Keys from a seeded PRNG are predictable. Use it for fixtures only; the
default `DataGenerator` draws from the OS CSPRNG, which is what any card
destined for a real network requires.
