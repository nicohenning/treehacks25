from crunchflow.input import InputFile
from Inference import InferenceRequest
from logger import setup_logger
import subprocess
import os
import pandas as pd
from crunchflow.output import TimeSeries

logger = setup_logger(__name__)


class Model:
    ASSETS_PATH = os.path.join(os.path.dirname(__file__), "assets")
    INPUT_FILE_NAME = "model.in"
    INPUT_FILE_MODIFIED = "model_modified.in"
    OUTPUT_PATH = "output"
    DOMAIN_LENGTH = 30
    FIXED_DEPTH = 0.25
    MOLECULAR_WEIGHT_CO2 = 44.01

    def __init__(self):
        pass

    def _convert_years_to_flows(self, years: int):
        """
        Converts the specified number of years to the corresponding number of flow steps.
        """
        return Model.DOMAIN_LENGTH / years

    def _compute_total_concentration(
        self, co2_series: pd.Series, porosity: float, area: float
    ):
        """
        Computes the total CO2 concentration in the specified domain.
        """
        co2_concentration = (
            co2_series.cumsum()
            * Model.FIXED_DEPTH
            * area
            * Model.MOLECULAR_WEIGHT_CO2
            * porosity
        )
        return co2_concentration

    def create_input(self, model_config: InferenceRequest):
        """
        Creates a new crunflow input tensor.
        """
        self.simulation = InputFile.load(self.INPUT_FILE_NAME, path=self.ASSETS_PATH)
        self.simulation.temperature.set_temperature = model_config.temperature
        self.simulation.flow.constant_flow = self._convert_years_to_flows(
            model_config.time_period
        )
        self.simulation.save(
            self.INPUT_FILE_MODIFIED, path=self.ASSETS_PATH, update_pestcontrol=True
        )

    def run_simulation(self, model_config: InferenceRequest):
        """
        Runs the crunchflow simulation with the specified model configuration.
        """
        self.create_input(model_config)
        os.chdir(self.ASSETS_PATH)
        subprocess.run(["crunchflow", self.INPUT_FILE_MODIFIED], check=True)
        porosity = self.simulation.porosity.fix_porosity
        ts = TimeSeries("totconhistory.txt")
        df = ts.df
        co2_series = df["Tracer"]
        concentration_ts = self._compute_total_concentration(
            co2_series, porosity, model_config.area
        )
        total_concentration = concentration_ts.iloc[-1]
        return concentration_ts, total_concentration
