from pydantic import BaseModel

class ContentIdentifyResponse(BaseModel):
    content: str
    brightness: str
