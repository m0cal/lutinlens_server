from pydantic import BaseModel, Field
class FramingResponse(BaseModel):
    ready_to_shoot: int
    suggestion: str | None
