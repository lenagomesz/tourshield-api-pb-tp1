from fastapi import APIRouter, Depends
from app.models import PredictRequest, PredictResponse
from app.security import current_user

router = APIRouter(tags=["predict"])


@router.post("/predict", response_model=PredictResponse)
def predict(payload: PredictRequest, username: str = Depends(current_user)):
    # Coordinates are untrusted input. No model, eligibility, or geofence decision here.
    # Do not persist or echo messages, tokens, or precise location.
    return PredictResponse()
