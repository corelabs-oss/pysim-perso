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
"""GSM Data Generator — public API."""
import multiprocessing
import os
import sys

from gsm_data_generator.base import __version__, DATAGENError
from gsm_data_generator import error

# ------------------------------------------------------------------ #
# Public API re-exports
# ------------------------------------------------------------------ #
from gsm_data_generator.generator.generate import DataGenerator
from gsm_data_generator.algorithm.encrypt import CryptoUtils, DependentDataGenerator
from gsm_data_generator.algorithm.encode import EncodingUtils
from gsm_data_generator.processor.process import DataProcessing, DataFrameProcessor
from gsm_data_generator.transform.transform import DataTransform
from gsm_data_generator.globals.parameters import Parameters, DataFrames
from gsm_data_generator.executor.script import DataGenerationScript
from gsm_data_generator.parser.utils import (
    json_loader,
    json_loader_2_ConfigHolder,
    ConfigHolder,
)

import gsm_data_generator.testing


def _should_print_backtrace() -> bool:
    in_pytest = "PYTEST_CURRENT_TEST" in os.environ
    raw = os.environ.get("DATAGEN_BACKTRACE", "0")
    try:
        return in_pytest or bool(int(raw))
    except ValueError:
        raise ValueError(
            f"Invalid value for DATAGEN_BACKTRACE '{raw}' — set to 0 or 1."
        )


def _wrap_excepthook(exception_hook):
    def wrapper(exctype, value, trbk):
        if exctype is error.DiagnosticError and not _should_print_backtrace():
            print("note: run with `DATAGEN_BACKTRACE=1` to display a backtrace.")
        else:
            exception_hook(exctype, value, trbk)
        for p in multiprocessing.active_children():
            p.terminate()

    return wrapper


sys.excepthook = _wrap_excepthook(sys.excepthook)

__all__ = [
    "__version__",
    "DATAGENError",
    # Generators
    "DataGenerator",
    # Crypto / encoding
    "CryptoUtils",
    "DependentDataGenerator",
    "EncodingUtils",
    # Processing / transformation
    "DataProcessing",
    "DataFrameProcessor",
    "DataTransform",
    # Global state
    "Parameters",
    "DataFrames",
    # High-level pipeline
    "DataGenerationScript",
    # Config loading
    "json_loader",
    "json_loader_2_ConfigHolder",
    "ConfigHolder",
]
