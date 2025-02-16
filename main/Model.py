from crunchflow.input import InputFile
from pydantic import BaseModel, Field, validator
from main.utils.logger import setup_logger
from main.utils.location_temp import (
    get_lat_lon_from_address,
    get_average_yearly_temperature,
)
import subprocess
import os
import pandas as pd
from crunchflow.output import TimeSeries
import numpy as np

logger = setup_logger(__name__)


class InferenceRequest(BaseModel):
    address: str = Field(..., description="Simulation address (must be non-empty)")
    feedstock_type: str = Field(..., description="Type of feed stock")
    area: float = Field(..., gt=0, description="Area must be greater than zero")
    time_period: int = Field(
        ..., gt=0, description="Time period (in years) must be greater than zero"
    )
    application_rate: float = Field(..., gt=0, description="Application rate")
    clay_pct: float = Field(..., gt=0, description="Clay percentage")
    silt_pct: float = Field(..., gt=0, description="Silt percentage")
    sand_pct: float = Field(..., gt=0, description="Sand percentage")

    @validator("address")
    def validate_address(cls, v):
        if not v.strip():
            raise ValueError("Address must not be empty or blank")
        return v

    @validator("feedstock_type")
    def validate_feedstock_type(cls, v):
        if v not in ["basalt", "larnite", "wollastonite"]:
            raise ValueError(
                "Feedstock type must be one of 'basalt', 'larnite', or 'wollastonite'"
            )
        return v

    @validator("clay_pct")
    def validate_clay_pct(cls, v):
        if v < 0 or v > 100:
            raise ValueError("Clay percentage must be between 0 and 100")
        return v

    @validator("silt_pct")
    def validate_silt_pct(cls, v):
        if v < 0 or v > 100:
            raise ValueError("Silt percentage must be between 0 and 100")
        return v

    @validator("sand_pct")
    def validate_sand_pct(cls, v):
        if v < 0 or v > 100:
            raise ValueError("Sand percentage must be between 0 and 100")
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
    FEEDSTOCK_DENSITIES = {
        "basalt": 2.9,
        "larnite": 3.3,
        "wollastonite": 2.8,
    }
    FEEDSTOCK_NAMES = {
        "basalt": "An50Ab50AS",
        "larnite": "Larnite",
        "wollastonite": "Wollastonite",
    }
    SOIL_NAMES = {
        "clay": "Kaolinite",
        "silt": "K-Feldspar",
        "sand": "Quartz",
    }

    def __init__(self):
        pass

    def _calculate_soil_bulk_density(
        self, clay_pct: float, silt_pct: float, sand_pct: float
    ):
        return 1.3 + 0.0045 * sand_pct - 0.0045 * clay_pct - 0.002 * silt_pct

    def _calculate_volume_fraction(
        self, feedstock_density: float, soil_density: float, application_rate: float
    ):
        mixing_depth = 30
        porosity = 0.4
        feedstock_mass_per_cm2 = application_rate * 0.01
        feedstock_volume = feedstock_mass_per_cm2 / feedstock_density
        soil_volume = mixing_depth * (1 - porosity) / soil_density
        return feedstock_volume / (soil_volume + feedstock_volume)

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

    def _handle_volume_fraction(self, feedstock_type: str, volume_fraction: float):
        zero_string = "0 ssa 0.5"
        if feedstock_type == "basalt":
            self.simulation.conditions["Feedstock"].concentrations[
                "An50Ab50AS"
            ] = f"{volume_fraction:.8} ssa 0.5"
            self.simulation.conditions["Feedstock"].concentrations[
                "Larnite"
            ] = zero_string
            self.simulation.conditions["Feedstock"].concentrations[
                "Wollastonite"
            ] = zero_string
        elif feedstock_type == "larnite":
            self.simulation.conditions["Feedstock"].concentrations[
                "An50Ab50AS"
            ] = zero_string
            self.simulation.conditions["Feedstock"].concentrations[
                "Larnite"
            ] = f"{volume_fraction:.8} ssa 0.5"
            self.simulation.conditions["Feedstock"].concentrations[
                "Wollastonite"
            ] = zero_string
        elif feedstock_type == "wollastonite":
            self.simulation.conditions["Feedstock"].concentrations[
                "An50Ab50AS"
            ] = zero_string
            self.simulation.conditions["Feedstock"].concentrations[
                "Larnite"
            ] = zero_string
            self.simulation.conditions["Feedstock"].concentrations[
                "Wollastonite"
            ] = f"{volume_fraction:.8} ssa 0.5"

    def _handle_native_soil(self, clay_pct: float, silt_pct: float, sand_pct: float):
        self.simulation.conditions["NativeSoil"].concentrations[
            "Kaolinite"
        ] = f"{clay_pct:.8} ssa 1"
        self.simulation.conditions["NativeSoil"].concentrations[
            "K-Feldspar"
        ] = f"{silt_pct:.8} ssa 0.1"
        self.simulation.conditions["NativeSoil"].concentrations[
            "Quartz"
        ] = f"{sand_pct:.8} ssa 0.1"

    def create_input(self, model_config: InferenceRequest):
        """
        Creates a new crunflow input tensor.
        """
        lat, lon = get_lat_lon_from_address(model_config.address)
        if lat is None or lon is None:
            raise ValueError(
                f"Could not get coordinates for address: {model_config.address}"
            )
        logger.info(f"Coordinates: {lat}, {lon}")

        temperature = get_average_yearly_temperature(lat, lon)
        if temperature is None:
            raise ValueError(f"Could not get temperature for coordinates: {lat}, {lon}")
        logger.info(f"Temperature: {temperature}")
        if model_config.feedstock_type not in self.FEEDSTOCK_DENSITIES:
            raise ValueError(
                f"Feedstock type not supported: {model_config.feedstock_type}"
            )
        feedstock_density = self.FEEDSTOCK_DENSITIES[model_config.feedstock_type]
        soil_density = self._calculate_soil_bulk_density(
            model_config.clay_pct, model_config.silt_pct, model_config.sand_pct
        )
        logger.info(f"Soil density: {soil_density}")
        volume_fraction = self._calculate_volume_fraction(
            feedstock_density, soil_density, model_config.application_rate
        )

        self.simulation = InputFile.load(self.INPUT_FILE_NAME, path=self.ASSETS_PATH)
        self.simulation.temperature.set_temperature = float(temperature)
        self.simulation.flow.constant_flow = self._convert_years_to_flows(
            model_config.time_period
        )
        logger.info(volume_fraction)
        self._handle_volume_fraction(model_config.feedstock_type, volume_fraction)
        self._handle_native_soil(
            model_config.clay_pct, model_config.silt_pct, model_config.sand_pct
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
        if model_config.clay_pct + model_config.silt_pct + model_config.sand_pct > 1:
            raise ValueError(
                "The sum of clay, silt, and sand percentages must not be greater than 1."
            )
        self.create_input(model_config)
        os.chdir(self.ASSETS_PATH)
        subprocess.run(["CrunchTope", self.INPUT_FILE_MODIFIED], check=True)
        porosity = 0.999999
        ts = TimeSeries("timeEW2m.out")
        df = ts.df
        co2_series = df["CO2(aq)"]
        concentration_ts = self._compute_total_concentration(
            co2_series, porosity, model_config.area
        )
        total_concentration = concentration_ts.iloc[-1]
        logger.info(f"Total concentration: {total_concentration}")
        logger.info(f"Concentration time series: {concentration_ts}")
        return concentration_ts, total_concentration
