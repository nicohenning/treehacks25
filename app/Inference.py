from pydantic import BaseModel


class InferenceRequest(BaseModel):
    address: str
    temperature: int
    feed_stock_type: str
    area: float
    time_period: int
