from main.Model import Model, InferenceRequest
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .utils.logger import setup_logger

app = FastAPI()
logger = setup_logger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"health": "Running"}


@app.post("/inference")
def run_inference(request: InferenceRequest):
    logger.info(f"Received inference request: {request}")
    try:
        model = Model()
        concentration_ts, total_concentration = model.run_simulation(request)
        return {
            "concentration_ts": concentration_ts.values.tolist(),
            "total_concentration": total_concentration,
        }
    except Exception as e:
        logger.error(f"Error running inference: {e}")
        return {"error": str(e)}
