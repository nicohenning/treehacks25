from crunchflow.input import InputFile
from Inference import InferenceRequest
from logger import setup_logger
import os

logger = setup_logger(__name__)


class Model:
    ASSETS_PATH = os.path.join(os.path.dirname(__file__), "assets")
    INPUT_FILE_NAME = "model.in"
    INPUT_FILE_MODIFIED = "model_modified.in"
    DOMAIN_LENGTH = 30

    def __init__(self):
        pass

    def _convert_years_to_flows(self, years: int):
        """
        Converts the specified number of years to the corresponding number of flow steps.
        """
        return Model.DOMAIN_LENGTH / years

    def create_input(self, model_config: InferenceRequest):
        """
        Creates a new crunflow input tensor.
        """
        simulation = InputFile.load(self.INPUT_FILE_NAME, path=self.ASSETS_PATH)
        simulation.temperature.set_temperature = model_config.temperature
        simulation.flow.constant_flow = self._convert_years_to_flows(
            model_config.time_period
        )
        simulation.save(self.INPUT_FILE_MODIFIED, path=self.ASSETS_PATH)
