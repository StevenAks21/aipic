from pydantic import BaseModel

class DetectionResponse(BaseModel):
    prediction: str
    confidence: float
