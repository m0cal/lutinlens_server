from pydantic import BaseModel, Field

class ContentIdentifyRequest(BaseModel):
    image_uri: str
