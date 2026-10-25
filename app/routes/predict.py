from fastapi import APIRouter, Depends
from app.models import PredictRequest, PredictResponse
from app.security import current_user

router = APIRouter(tags=["predict"])


@router.post("/predict", response_model=PredictResponse, summary="Validar mensagem sem inferência",
             description="Requer Bearer. Mensagem de 1-4.000 caracteres, coordenadas opcionais em par. Retorna placeholder sem autorizar benefício.",
             responses={401: {"description": "Bearer ausente ou inválido"}, 422: {"description": "Mensagem, coordenadas ou campo extra inválido"}})
def predict(payload: PredictRequest, username: str = Depends(current_user)):
    # Coordinates are untrusted input. No model, eligibility, or geofence decision here.
    # Do not persist or echo messages, tokens, or precise location.
    return PredictResponse()
