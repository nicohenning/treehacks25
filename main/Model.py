from crunchflow.input import InputFile
from pydantic import BaseModel, Field, validator
from main.utils.logger import setup_logger
import subprocess
import os
import pandas as pd
from crunchflow.output import TimeSeries
import numpy as np

logger = setup_logger(__name__)


class InferenceRequest(BaseModel):
    address: str = Field(..., description="Simulation address (must be non-empty)")
    temperature: int = Field(..., description="Temperature (in Celsius)")
    feed_stock_type: str = Field(..., description="Type of feed stock")
    area: float = Field(..., gt=0, description="Area must be greater than zero")
    time_period: int = Field(
        ..., gt=0, description="Time period (in years) must be greater than zero"
    )

    @validator("address")
    def validate_address(cls, v):
        if not v.strip():
            raise ValueError("Address must not be empty or blank")
        return v

    @validator("temperature")
    def validate_temperature(cls, v):
        if v < -273:
            raise ValueError("Temperature must be above -273°C (absolute zero)")
        return v


class Model:
    ASSETS_PATH = os.path.join(os.path.dirname(__file__), "assets")
    INPUT_FILE_NAME = "model.in"
    INPUT_FILE_MODIFIED = "model_modified.in"
    OUTPUT_PATH = "output"
    DOMAIN_LENGTH = 30
    FIXED_DEPTH = 0.25
    MOLECULAR_WEIGHT_CO2 = 44.01
    CO_2_DENSITY = 1.98

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
        co2_values = co2_series.astype(np.float64)
        co2_concentration = (
            co2_values.cumsum()
            * Model.FIXED_DEPTH
            * area
            * Model.MOLECULAR_WEIGHT_CO2
            * porosity
            * Model.CO_2_DENSITY
        )
        return co2_concentration

    def create_input(self, model_config: InferenceRequest):
        """
        Creates a new crunflow input tensor.
        """
        self.simulation = InputFile.load(self.INPUT_FILE_NAME, path=self.ASSETS_PATH)
        self.simulation.temperature.set_temperature = float(model_config.temperature)
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
        if model_config.time_period <= 0:
            raise ValueError("The time period must be greater than zero.")
        self.create_input(model_config)
        os.chdir(self.ASSETS_PATH)
        subprocess.run(["CrunchTope", self.INPUT_FILE_MODIFIED], check=True)
        porosity = float(self.simulation.porosity.fix_porosity)
        ts = TimeSeries("totconhistory.txt")
        df = ts.df
        co2_series = df["Tracer"]
        concentration_ts = self._compute_total_concentration(
            co2_series, porosity, model_config.area
        )
        total_concentration = concentration_ts.iloc[-1]
        logger.info(f"Total concentration: {total_concentration}")
        logger.info(f"Concentration time series: {concentration_ts}")
        return concentration_ts, total_concentration
