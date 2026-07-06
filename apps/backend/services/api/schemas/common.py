from pydantic import BaseModel


class MutationMeta(BaseModel):
    message: str


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "nova-api"
    version: str = "0.1.0"


class OkResponse(BaseModel):
    ok: bool = True
