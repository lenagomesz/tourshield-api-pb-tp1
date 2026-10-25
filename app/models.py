from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator, model_validator


class StrictInput(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class AuthInput(StrictInput):
    username: str = Field(min_length=1, max_length=128)
    password: SecretStr = Field(min_length=1, max_length=1024)
    grant_type: str = Field(default="password", pattern="^password$")
    scope: str = Field(default="", max_length=0)
    client_id: str | None = Field(default=None, max_length=128)
    client_secret: SecretStr | None = None


class ReservationInput(StrictInput):
    destination: str = Field(min_length=1, max_length=120)

    @field_validator("destination")
    @classmethod
    def nonblank_destination(cls, value):
        if not value.strip():
            raise ValueError("Destino vazio")
        return value.strip()


class ReservationResponse(BaseModel):
    id: str
    destination: str
    status: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 900


class PredictRequest(StrictInput):
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
