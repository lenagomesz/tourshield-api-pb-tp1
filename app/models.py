from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 900


class PredictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    message: str = Field(min_length=1, max_length=4000)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)

    @field_validator("message")
    @classmethod
    def nonblank(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("Mensagem não pode estar vazia")
        return value

    @model_validator(mode="after")
    def paired_coordinates(self):
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("Informe latitude e longitude juntas")
        return self


class PredictResponse(BaseModel):
    intent: str | None = None
    status: str = "placeholder"
    detail: str = "Modelo não implementado; nenhum benefício ou reserva foi autorizado."
