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
import pandas as pd
from threading import Lock


class DataFrames:
    """Singleton holding the shared input and output DataFrames."""

    __instance = None

    def __init__(self):
        if DataFrames.__instance is not None:
            raise RuntimeError("DataFrames is a singleton — use get_instance().")
        DataFrames.__instance = self
        self.__INPUT_DF = pd.DataFrame()
        self.ELECT_DF = pd.DataFrame()
        self.GRAPH_DF = pd.DataFrame()
        self.SERVER_DF = pd.DataFrame()
        self.__KEYS: dict = {}

    @staticmethod
    def get_instance() -> "DataFrames":
        if DataFrames.__instance is None:
            DataFrames.__instance = DataFrames()
        return DataFrames.__instance

    def set_input_df(self, value: pd.DataFrame) -> None:
        self.__INPUT_DF = value

    def get_input_df(self) -> pd.DataFrame:
        return self.__INPUT_DF

    def set_KEYS(self, value: dict) -> None:
        self.__KEYS = value

    def get_KEYS(self) -> dict:
        return self.__KEYS


class Parameters(DataFrames):
    """Thread-safe singleton holding all in-flight SIM card configuration parameters."""

    __instance = None
    __lock = Lock()

    def __init__(self):
        super().__init__()
        if Parameters.__instance is not None:
            raise RuntimeError("Parameters is a singleton — use get_instance().")
        Parameters.__instance = self

        # SIM card parameters
        self.__ICCID: str = ""
        self.__IMSI: str = ""
        self.__PIN1: str = ""
        self.__PUK1: str = ""
        self.__PIN2: str = ""
        self.__PUK2: str = ""
        self.__K4: str = ""
        self.__OP: str = ""
        self.__ADM1: str = ""
        self.__ADM6: str = ""
        self.__ACC: str = ""
        self.__DATA_SIZE: str = ""

        # File paths
        self.__TEMPLATE_JSON: str = ""
        self.__INPUT_FILE_PATH: str = ""
        self.__OUTPUT_FILES_DIR: str = ""
        self.file_name: str = ""

        # Output type enable flags
        self.__ELECT_CHECK: bool = False
        self.__GRAPH_CHECK: bool = False
        self.__SERVER_CHECK: bool = False

        # Randomisation flags — True means use fixed value, False means generate randomly
        self.__pin1_rand: bool = True
        self.__puk1_rand: bool = True
        self.__pin2_rand: bool = True
        self.__puk2_rand: bool = True
        self.__adm1_rand: bool = True
        self.__adm6_rand: bool = True
        self.__acc_rand: bool = True

        # Output variable dictionaries
        self.__ELECT_DICT: dict = {}
        self.__GRAPH_DICT: dict = {}
        self.__SERVER_DICT: dict = {}

        # Column separators used when writing output files
        self.__ELECT_SEP: str = ""
        self.__GRAPH_SEP: str = ""
        self.__SERVR_SEP: str = ""

    @classmethod
    def get_instance(cls) -> "Parameters":
        with cls.__lock:
            if cls.__instance is None:
                cls.__instance = Parameters()
            return cls.__instance

    # ------------------------------------------------------------------ #
    # Separators
    # ------------------------------------------------------------------ #

    @property
    def ELECT_SEP(self) -> str:
        return self.__ELECT_SEP

    @ELECT_SEP.setter
    def ELECT_SEP(self, value: str) -> None:
        self.__ELECT_SEP = value

    @property
    def GRAPH_SEP(self) -> str:
        return self.__GRAPH_SEP

    @GRAPH_SEP.setter
    def GRAPH_SEP(self, value: str) -> None:
        self.__GRAPH_SEP = value

    @property
    def SERVER_SEP(self) -> str:
        return self.__SERVR_SEP

    @SERVER_SEP.setter
    def SERVER_SEP(self, value: str) -> None:
        self.__SERVR_SEP = value

    @property
    def SERVR_SEP(self) -> str:
        return self.__SERVR_SEP

    @SERVR_SEP.setter
    def SERVR_SEP(self, value: str) -> None:
        self.__SERVR_SEP = value

    # ------------------------------------------------------------------ #
    # File paths
    # ------------------------------------------------------------------ #

    @property
    def TEMPLATE_JSON(self) -> str:
        return self.__TEMPLATE_JSON

    @TEMPLATE_JSON.setter
    def TEMPLATE_JSON(self, value: str) -> None:
        self.__TEMPLATE_JSON = value

    @property
    def INPUT_FILE_PATH(self) -> str:
        return self.__INPUT_FILE_PATH

    @INPUT_FILE_PATH.setter
    def INPUT_FILE_PATH(self, value: str) -> None:
        self.__INPUT_FILE_PATH = value

    @property
    def OUTPUT_FILES_DIR(self) -> str:
        return self.__OUTPUT_FILES_DIR

    @OUTPUT_FILES_DIR.setter
    def OUTPUT_FILES_DIR(self, value: str) -> None:
        self.__OUTPUT_FILES_DIR = value

    # ------------------------------------------------------------------ #
    # SIM parameters
    # ------------------------------------------------------------------ #

    @property
    def ICCID(self) -> str:
        return self.__ICCID

    @ICCID.setter
    def ICCID(self, value: str) -> None:
        self.__ICCID = value

    @property
    def IMSI(self) -> str:
        return self.__IMSI

    @IMSI.setter
    def IMSI(self, value: str) -> None:
        self.__IMSI = value

    @property
    def PIN1(self) -> str:
        return self.__PIN1

    @PIN1.setter
    def PIN1(self, value: str) -> None:
        self.__PIN1 = value

    @property
    def PUK1(self) -> str:
        return self.__PUK1

    @PUK1.setter
    def PUK1(self, value: str) -> None:
        self.__PUK1 = value

    @property
    def PIN2(self) -> str:
        return self.__PIN2

    @PIN2.setter
    def PIN2(self, value: str) -> None:
        self.__PIN2 = value

    @property
    def PUK2(self) -> str:
        return self.__PUK2

    @PUK2.setter
    def PUK2(self, value: str) -> None:
        self.__PUK2 = value

    @property
    def OP(self) -> str:
        return self.__OP

    @OP.setter
    def OP(self, value: str) -> None:
        self.__OP = value

    @property
    def K4(self) -> str:
        return self.__K4

    @K4.setter
    def K4(self, value: str) -> None:
        self.__K4 = value

    @property
    def ADM1(self) -> str:
        return self.__ADM1

    @ADM1.setter
    def ADM1(self, value: str) -> None:
        self.__ADM1 = value

    @property
    def ADM6(self) -> str:
        return self.__ADM6

    @ADM6.setter
    def ADM6(self, value: str) -> None:
        self.__ADM6 = value

    @property
    def ACC(self) -> str:
        return self.__ACC

    @ACC.setter
    def ACC(self, value: str) -> None:
        self.__ACC = value

    @property
    def DATA_SIZE(self) -> str:
        return self.__DATA_SIZE

    @DATA_SIZE.setter
    def DATA_SIZE(self, value: str) -> None:
        self.__DATA_SIZE = value

    # ------------------------------------------------------------------ #
    # Output type enable flags
    # ------------------------------------------------------------------ #

    @property
    def ELECT_CHECK(self) -> bool:
        return self.__ELECT_CHECK

    @ELECT_CHECK.setter
    def ELECT_CHECK(self, value: bool) -> None:
        self.__ELECT_CHECK = value

    @property
    def GRAPH_CHECK(self) -> bool:
        return self.__GRAPH_CHECK

    @GRAPH_CHECK.setter
    def GRAPH_CHECK(self, value: bool) -> None:
        self.__GRAPH_CHECK = value

    @property
    def SERVER_CHECK(self) -> bool:
        return self.__SERVER_CHECK

    @SERVER_CHECK.setter
    def SERVER_CHECK(self, value: bool) -> None:
        self.__SERVER_CHECK = value

    # ------------------------------------------------------------------ #
    # Randomisation flags
    # ------------------------------------------------------------------ #

    @property
    def PIN1_RAND(self) -> bool:
        return self.__pin1_rand

    @PIN1_RAND.setter
    def PIN1_RAND(self, value: bool) -> None:
        self.__pin1_rand = value

    @property
    def PUK1_RAND(self) -> bool:
        return self.__puk1_rand

    @PUK1_RAND.setter
    def PUK1_RAND(self, value: bool) -> None:
        self.__puk1_rand = value

    @property
    def PIN2_RAND(self) -> bool:
        return self.__pin2_rand

    @PIN2_RAND.setter
    def PIN2_RAND(self, value: bool) -> None:
        self.__pin2_rand = value

    @property
    def PUK2_RAND(self) -> bool:
        return self.__puk2_rand

    @PUK2_RAND.setter
    def PUK2_RAND(self, value: bool) -> None:
        self.__puk2_rand = value

    @property
    def ADM1_RAND(self) -> bool:
        return self.__adm1_rand

    @ADM1_RAND.setter
    def ADM1_RAND(self, value: bool) -> None:
        self.__adm1_rand = value

    @property
    def ADM6_RAND(self) -> bool:
        return self.__adm6_rand

    @ADM6_RAND.setter
    def ADM6_RAND(self, value: bool) -> None:
        self.__adm6_rand = value

    @property
    def ACC_RAND(self) -> bool:
        return self.__acc_rand

    @ACC_RAND.setter
    def ACC_RAND(self, value: bool) -> None:
        self.__acc_rand = value

    # ------------------------------------------------------------------ #
    # Output variable dictionaries
    # ------------------------------------------------------------------ #

    @property
    def ELECT_DICT(self) -> dict:
        return self.__ELECT_DICT

    @ELECT_DICT.setter
    def ELECT_DICT(self, value: dict) -> None:
        self.__ELECT_DICT = value

    @property
    def GRAPH_DICT(self) -> dict:
        return self.__GRAPH_DICT

    @GRAPH_DICT.setter
    def GRAPH_DICT(self, value: dict) -> None:
        self.__GRAPH_DICT = value

    @property
    def SERVER_DICT(self) -> dict:
        return self.__SERVER_DICT

    @SERVER_DICT.setter
    def SERVER_DICT(self, value: dict) -> None:
        self.__SERVER_DICT = value

    # ------------------------------------------------------------------ #
    # Validation
    # ------------------------------------------------------------------ #

    @staticmethod
    def is_valid(param, param_name: str) -> bool:
        """Return True if `param` satisfies the length/format rule for `param_name`."""
        match param_name:
            case "ICCID":
                return len(str(param)) in (18, 19, 20)
            case "IMSI":
                return len(str(param)) == 15
            case "PIN1" | "PIN2":
                return len(str(param)) == 4
            case "PUK1" | "PUK2" | "ADM1" | "ADM6":
                return len(str(param)) == 8
            case "OP":
                return len(str(param)) == 32
            case "K4":
                return len(str(param)) in (32, 64)
            case "SIZE":
                return int(param) > 0
            case "DICT":
                return len(dict(param)) > 0
            case _:
                return False

    @staticmethod
    def is_valid_df(param, param_name: str) -> bool:
        """Return True if the DataFrame is empty (i.e. not yet populated)."""
        if param_name == "DF":
            return pd.DataFrame(param).empty
        return False

    def check_params(self) -> bool:
        """Return True if all required SIM parameters pass format validation."""
        return (
            self.is_valid(self.IMSI, "IMSI")
            and self.is_valid(self.ICCID, "ICCID")
            and self.is_valid(self.DATA_SIZE, "SIZE")
            and self.is_valid(self.PIN1, "PIN1")
            and self.is_valid(self.PUK1, "PUK1")
            and self.is_valid(self.PIN2, "PIN2")
            and self.is_valid(self.PUK2, "PUK2")
            and self.is_valid(self.ADM1, "ADM1")
            and self.is_valid(self.ADM6, "ADM6")
            and self.is_valid(self.OP, "OP")
            and self.is_valid(self.K4, "K4")
            and self.is_valid(self.ELECT_DICT, "DICT")
            and self.is_valid(self.GRAPH_DICT, "DICT")
        )

    def get_all_params_dict(self) -> dict:
        return {
            "OP": self.OP,
            "K4": self.K4,
            "ICCID": self.ICCID,
            "IMSI": self.IMSI,
            "PIN1": self.PIN1,
            "PUK1": self.PUK1,
            "PIN2": self.PIN2,
            "PUK2": self.PUK2,
            "ADM1": self.ADM1,
            "ADM6": self.ADM6,
            "ACC": self.ACC,
            "DATA_SIZE": self.DATA_SIZE,
        }

    def print_all_global_parameters(self) -> None:
        """Print all major configuration parameters (for debugging)."""
        print("======= Current Global Parameters =======")
        for key, value in self.get_all_params_dict().items():
            print(f"  {key}: {value}")
        print(f"  ELECT_DICT: {self.ELECT_DICT}")
        print(f"  GRAPH_DICT: {self.GRAPH_DICT}")
        print(f"  SERVER_DICT: {self.SERVER_DICT}")


__all__ = ["Parameters", "DataFrames"]
