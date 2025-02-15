from Model import Model
from fastapi import FastAPI
from Inference import InferenceRequest
from logger import setup_logger

app = FastAPI()
logger = setup_logger(__name__)


@app.get("/")
def read_root():
    return {"health": "Running"}


@app.post("/inference")
def run_inference(request: InferenceRequest):
    logger.info(f"Received inference request: {request}")
    model = Model()
    model.create_input(request)
    return {"inference": "running"}
