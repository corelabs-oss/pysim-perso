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
"""End-to-end SIM personalization run.

:class:`DataGenerationScript` is the top-level entry point. A run has four
stages, and the methods below are ordered to follow them:

1. **Configure** — :meth:`~DataGenerationScript.json_to_global_params` copies
   the validated config into :class:`Parameters`.
2. **Validate** — :meth:`~DataGenerationScript.run_prod_check`, when the config
   opts in.
3. **Generate** — :meth:`~DataGenerationScript.generate_all_data` builds one
   frame per enabled output. Nothing touches disk in this stage.
4. **Write** — :meth:`~DataGenerationScript.write_outputs` writes the frames
   and records the batch in the issuance ledger.
"""

from typing import Callable, NamedTuple

import pandas as pd

from ..algorithm import CryptoUtils, DependentDataGenerator
from ..error import ConfigValidationError
from ..issuance import IssuanceLedger
from ..processor import DataProcessing, DataFrameProcessor
from ..globals import DataFrames, Parameters
from ..generator import DataGenerator
from ..utils import copy_function, list_2_dict, DEFAULT_HEADER
from ..writer import OutputWriter

# An IMSI is MCC (always 3 digits) + MNC (2 or 3) + MSIN. The first 5 digits
# are therefore structural under every numbering plan, so incrementing must
# never carry into them — that would move the batch to a different operator.
# This is a deliberately conservative bound: where the MNC is 3 digits (the
# North American Numbering Plan) its final digit is not covered.
IMSI_FIXED_PREFIX_LENGTH = 5

# OTA keysets, in the order they are written to the frame.
OTA_KEYSET_COLUMNS = tuple(
    f"{key}{index}" for index in range(1, 4) for key in ("KIC", "KID", "KIK")
)


class _OutputSpec(NamedTuple):
    """How one output type is derived from the generated frame."""

    enabled: bool
    columns: dict
    clip: bool
    encode: bool


class DataGenerationScript:
    """One personalization run, owning its own parameter state.

    Independent runs can therefore proceed concurrently in a single process.
    See the module docstring for the stage ordering.
    """

    # ------------------------------------------------------------------ #
    # Construction
    # ------------------------------------------------------------------ #

    def __init__(
        self,
        config_holder,
        params=None,
        data_generator=None,
        ledger=None,
    ):
        """Create a generation run.

        Parameters
        ----------
        config_holder
            Validated configuration, from :func:`json_loader` or
            :func:`json_loader_2_ConfigHolder`.
        params
            Parameter state to operate on. Defaults to a fresh
            :class:`Parameters` owned by this script. Scripts previously shared
            one process-wide instance, so the last ``json_to_global_params()``
            call in a process silently won for every script — pass an explicit
            instance only if you deliberately want shared state.
        data_generator
            Source of random SIM secrets. Defaults to :class:`DataGenerator`,
            which draws from :mod:`secrets`. Injecting an alternative allows a
            seeded, reproducible generator for testing; never use one to
            produce cards for real networks.
        ledger
            :class:`IssuanceLedger` used by :meth:`write_outputs` to refuse
            re-issuing identifiers. Defaults to one in the configured output
            directory.
        """
        self.config_holder = config_holder
        self.params = params if params is not None else Parameters()
        # Parameters extends DataFrames, so one object backs both roles.
        self.dataframes = self.params

        # Collaborators. All are stateless; they are attributes so that a
        # caller can substitute an alternative implementation.
        self.crypto_utils = CryptoUtils()
        self.data_generator = (
            data_generator if data_generator is not None else DataGenerator()
        )
        self.data_processor = DataProcessing()
        self.df_processor = DataFrameProcessor()
        self.dep_data_generator = DependentDataGenerator()

        self._ledger = ledger

    # ------------------------------------------------------------------ #
    # Stage 1 — configuration
    # ------------------------------------------------------------------ #

    def json_to_global_params(self) -> None:
        """Load configuration values from the config holder into the Parameters singleton."""
        disp = self.config_holder.DISP
        parameters = self.config_holder.PARAMETERS

        # Batch-wide operator material and identifier starting points.
        self.params.K4 = disp.K4
        self.params.OP = disp.op
        self.params.IMSI = disp.imsi
        self.params.ICCID = disp.iccid
        self.params.DATA_SIZE = disp.size

        # Cardholder and administrative codes. Each is used only when the
        # matching *_RAND flag below is set; otherwise a value is drawn per card.
        self.params.PIN1 = disp.pin1
        self.params.PUK1 = disp.puk1
        self.params.PIN2 = disp.pin2
        self.params.PUK2 = disp.puk2
        self.params.ADM1 = disp.adm1
        self.params.ADM6 = disp.adm6

        # Despite the name, *_RAND true means "use the fixed value above".
        # It mirrors the config's *_fix flags.
        self.params.PIN1_RAND = disp.pin1_fix
        self.params.PUK1_RAND = disp.puk1_fix
        self.params.PIN2_RAND = disp.pin2_fix
        self.params.PUK2_RAND = disp.puk2_fix
        self.params.ADM1_RAND = disp.adm1_fix
        self.params.ADM6_RAND = disp.adm6_fix

        # Which outputs to produce, and the column layout of each.
        self.params.ELECT_CHECK = disp.elect_check
        self.params.GRAPH_CHECK = disp.graph_check
        self.params.SERVER_CHECK = disp.server_check

        self.params.ELECT_DICT = list_2_dict(parameters.data_variables)
        self.params.GRAPH_DICT = parameters.laser_variables
        self.params.SERVER_DICT = list_2_dict(parameters.server_variables)

        self.params.ELECT_SEP = disp.elect_data_sep
        self.params.GRAPH_SEP = disp.graph_data_sep
        self.params.SERVER_SEP = disp.server_data_sep

    # ------------------------------------------------------------------ #
    # Stage 2 — validation
    # ------------------------------------------------------------------ #

    def run_prod_check(self) -> None:
        """Validate all parameters when ``prod_check`` is enabled in the config.

        Does nothing when ``prod_check`` is false, preserving the previous
        behaviour for configs that opt out.

        Raises
        ------
        ConfigValidationError
            If any parameter fails validation. The message lists every failure.
        """
        if not getattr(self.config_holder.DISP, "prod_check", False):
            return

        failures = self.params.validate_params()
        if failures:
            raise ConfigValidationError(
                "Parameter validation failed (prod_check is enabled):\n  - "
                + "\n  - ".join(failures)
            )

    # ------------------------------------------------------------------ #
    # Stage 3a — per-card values
    # ------------------------------------------------------------------ #

    def generate_eki(self, ki: str) -> str:
        """Ki encrypted under the batch transport key K4."""
        return self.dep_data_generator.calculate_eki(self.params.K4, ki)

    def generate_opc(self, ki: str) -> str:
        """OPc derived from this card's Ki and the batch OP."""
        return self.dep_data_generator.calculate_opc(self.params.OP, ki)

    def _fixed_or_random(self, name: str, generate: Callable[[], str]) -> str:
        """Return the configured value for *name*, or a fresh random one.

        ``<name>_RAND`` selects between them: true means the fixed value
        stored under ``<name>`` is used for every card in the batch.
        """
        if getattr(self.params, f"{name}_RAND"):
            return getattr(self.params, name)
        return generate()

    def generate_pin(self, pin_type: str) -> str:
        """Return the fixed PIN value if *_RAND is True, else generate a random 4-digit PIN."""
        return self._fixed_or_random(pin_type, self.data_generator.generate_4_digit)

    def generate_puk(self, puk_type: str) -> str:
        """Return the fixed PUK value if *_RAND is True, else generate a random 8-digit PUK."""
        return self._fixed_or_random(puk_type, self.data_generator.generate_8_digit)

    def generate_adm(self, adm_type: str) -> str:
        """Return the fixed ADM value if *_RAND is True, else generate a random 8-digit ADM."""
        return self._fixed_or_random(adm_type, self.data_generator.generate_8_digit)

    # ------------------------------------------------------------------ #
    # Stage 3b — frame assembly
    # ------------------------------------------------------------------ #

    def _apply_function(self, df: pd.DataFrame, dest: str, src: str, function) -> None:
        """Fill *dest* from *src* through *function*, if *dest* was requested."""
        if dest in df.columns:
            df[dest] = df[src].apply(function).copy(deep=False)

    def apply_functions(self, df: pd.DataFrame) -> pd.DataFrame:
        """Populate every per-card column of an initialised frame."""
        # Identifiers were sequenced upstream; normalise them to str.
        df["ICCID"] = df["ICCID"].apply(lambda x: copy_function(x))
        df["IMSI"] = df["IMSI"].apply(lambda x: copy_function(x))

        # Cardholder and administrative codes: fixed per batch or per card.
        df["PIN1"] = df["PIN1"].apply(lambda x: self.generate_pin("PIN1"))
        df["PIN2"] = df["PIN2"].apply(lambda x: self.generate_pin("PIN2"))
        df["PUK1"] = df["PUK1"].apply(lambda x: self.generate_puk("PUK1"))
        df["PUK2"] = df["PUK2"].apply(lambda x: self.generate_puk("PUK2"))
        df["ADM1"] = df["ADM1"].apply(lambda x: self.generate_adm("ADM1"))
        df["ADM6"] = df["ADM6"].apply(lambda x: self.generate_adm("ADM6"))

        # Subscriber key, then everything derived from it or from the IMSI.
        df["KI"] = df["KI"].apply(lambda x: self.data_generator.generate_ki())
        df["ACC"] = df["IMSI"].apply(
            lambda imsi: self.dep_data_generator.calculate_acc(imsi=str(imsi))
        )
        self._apply_function(df, "EKI", "KI", self.generate_eki)
        self._apply_function(df, "OPC", "KI", self.generate_opc)

        # OTA keysets are independent of Ki; the KI column is only a length source.
        for col in OTA_KEYSET_COLUMNS:
            if col in df.columns:
                df[col] = df["KI"].apply(lambda x: self.data_generator.generate_otas())

        return df

    def generate_demo_data(self) -> pd.DataFrame:
        """Build a frame of ``DATA_SIZE`` cards from the configured start values."""
        df = self.df_processor.generate_empty_dataframe(
            DEFAULT_HEADER, self.params.DATA_SIZE
        )
        # Identifiers are sequenced as fixed-width digit strings so that
        # leading zeros survive and a carry cannot reach the structural
        # prefix. See DataFrameProcessor.initialize_identifier_column.
        self.df_processor.initialize_identifier_column(df, "ICCID", self.params.ICCID)
        self.df_processor.initialize_identifier_column(
            df, "IMSI", self.params.IMSI, prefix_length=IMSI_FIXED_PREFIX_LENGTH
        )
        self.df_processor.initialize_column(df, "OP", self.params.OP, increment=False)
        self.df_processor.initialize_column(df, "K4", self.params.K4, increment=False)
        return self.apply_functions(df)

    def generate_non_demo_data(self) -> pd.DataFrame:
        """Build a frame from caller-supplied ICCID/IMSI columns.

        Not reachable through :meth:`generate_initial_data` yet.
        """
        input_df = self.dataframes.get_input_df()
        df = self.df_processor.generate_empty_dataframe(DEFAULT_HEADER, len(input_df))
        self.df_processor.initialize_column(df, "OP", self.params.OP, increment=False)
        self.df_processor.initialize_column(df, "K4", self.params.K4, increment=False)
        df["ICCID"] = input_df["ICCID"]
        df["IMSI"] = input_df["IMSI"]
        return self.apply_functions(df)

    def generate_initial_data(self, is_demo: bool):
        """Generate the base frame and return it with the batch keys."""
        try:
            if is_demo:
                demo_data = self.generate_demo_data()
                k4 = self.params.K4
                op = self.params.OP
                if not k4 or not isinstance(k4, str):
                    raise ValueError(
                        "Invalid value for K4: must be a non-empty string."
                    )
                if not op or not isinstance(op, str):
                    raise ValueError(
                        "Invalid value for OP: must be a non-empty string."
                    )
                return demo_data, {"k4": k4, "op": op}
            else:
                raise NotImplementedError(
                    "Non-demo data generation is not yet implemented."
                )
        except Exception as e:
            raise RuntimeError(f"Error in generate_initial_data: {e}") from e

    # ------------------------------------------------------------------ #
    # Stage 3c — pipeline
    # ------------------------------------------------------------------ #

    def process_final_data(
        self,
        input_dict: dict,
        df_input: pd.DataFrame,
        clip: bool,
        encoding: bool,
    ) -> pd.DataFrame:
        """Shape the generated frame into one output's column layout."""
        df = df_input.copy(deep=True)
        if encoding:
            df = self.df_processor.encode_dataframe(df)
        headers, _, _, _, left_ranges, right_ranges = (
            self.data_processor.extract_parameter_info(input_dict)
        )
        # Derived from the requested headers rather than hardcoded: a fixed
        # ceiling of 10 made an 11th repetition of the same column fail with
        # "['ICCID10'] not in index" instead of producing the column.
        duplicate_limit = (
            self.data_processor.max_duplicate_suffix(headers, df.columns) + 1
        )
        df = self.df_processor.add_duplicate_columns(df, duplicate_limit, headers)
        if clip:
            df = self.df_processor.clip_columns(df, left_ranges, right_ranges)
        return df

    def _output_specs(self) -> dict[str, _OutputSpec]:
        """Per-output derivation rules, in the order outputs are produced."""
        return {
            "SERVER": _OutputSpec(
                enabled=self.params.SERVER_CHECK,
                columns=self.params.SERVER_DICT,
                clip=False,
                encode=False,
            ),
            "GRAPH": _OutputSpec(
                enabled=self.params.GRAPH_CHECK,
                columns=self.params.GRAPH_DICT,
                clip=True,
                encode=False,
            ),
            "ELECT": _OutputSpec(
                enabled=self.params.ELECT_CHECK,
                columns=self.params.ELECT_DICT,
                clip=False,
                encode=True,
            ),
        }

    def generate_all_data(self) -> tuple[dict, dict]:
        """Run the full data generation pipeline.

        Returns
        -------
        tuple[dict, dict]
            (result_dfs, keys_dict) where result_dfs maps output type
            ('ELECT', 'GRAPH', 'SERVER') to its DataFrame, and keys_dict
            contains {'k4': ..., 'op': ...}.

        Raises
        ------
        ConfigValidationError
            If ``prod_check`` is enabled and any parameter fails validation.
        """
        self.run_prod_check()

        initial_df, keys_dict = self.generate_initial_data(True)

        result_dfs = {}
        for data_type, spec in self._output_specs().items():
            if not spec.enabled:
                continue
            if not spec.columns or not isinstance(spec.columns, dict):
                raise ValueError(
                    f"{data_type} is enabled but its variable dictionary is missing or invalid."
                )
            try:
                result_dfs[data_type] = self.process_final_data(
                    spec.columns, initial_df, spec.clip, spec.encode
                )
            except Exception as e:
                raise RuntimeError(f"Failed processing {data_type} data: {e}") from e

        return result_dfs, keys_dict

    # ------------------------------------------------------------------ #
    # Stage 4 — output
    # ------------------------------------------------------------------ #

    @property
    def ledger(self) -> IssuanceLedger:
        """Issuance ledger for this run, kept in the configured output dir."""
        if self._ledger is None:
            self._ledger = IssuanceLedger(self.config_holder.PATHS.OUTPUT_FILES_DIR)
        return self._ledger

    def issued_ranges(self) -> dict:
        """Return the ICCID and IMSI ranges this configuration covers."""
        size = int(self.params.DATA_SIZE)
        iccid_start, iccid_end = self.df_processor.sequence_bounds(
            self.params.ICCID, size, label="ICCID"
        )
        imsi_start, imsi_end = self.df_processor.sequence_bounds(
            self.params.IMSI, size, IMSI_FIXED_PREFIX_LENGTH, label="IMSI"
        )
        return {
            "iccid_start": iccid_start,
            "iccid_end": iccid_end,
            "imsi_start": imsi_start,
            "imsi_end": imsi_end,
            "size": size,
        }

    def write_outputs(
        self,
        result_dfs: dict,
        check_issuance: bool = True,
        include_header: bool = True,
    ) -> dict:
        """Write generated frames to the configured output directory.

        This is the point at which a batch counts as *issued*, so it is also
        where the issuance ledger is consulted and updated: the ledger is
        checked before anything is written and recorded only once every file
        has been written successfully. Generating frames in memory does not
        touch the ledger.

        Returns
        -------
        dict
            Mapping of output type to the path written.

        Raises
        ------
        IssuanceOverlapError
            If `check_issuance` is set and these identifiers were issued before.
        """
        paths = self.config_holder.PATHS
        ranges = self.issued_ranges()

        if check_issuance:
            self.ledger.check(
                ranges["iccid_start"],
                ranges["iccid_end"],
                ranges["imsi_start"],
                ranges["imsi_end"],
            )

        writer = OutputWriter(
            output_dir=paths.OUTPUT_FILES_DIR,
            file_name=paths.FILE_NAME,
            laser_ext=paths.OUTPUT_FILES_LASER_EXT,
            separators={
                "ELECT": self.params.ELECT_SEP,
                "GRAPH": self.params.GRAPH_SEP,
                "SERVER": self.params.SERVER_SEP,
            },
            include_header=include_header,
        )
        written = writer.write(result_dfs)

        if check_issuance:
            self.ledger.record(**ranges)

        return written


__all__ = ["DataGenerationScript"]
