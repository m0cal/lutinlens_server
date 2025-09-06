from pydantic import BaseModel, Field

class FramingRequest(BaseModel):
    session_id: str = Field(description="The unique identifier for a user's session.")
    img: str = Field(description="Base64 encoded img")
