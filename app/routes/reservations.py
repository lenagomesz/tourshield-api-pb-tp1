from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from app.database import Reservation, connect
from app.models import ReservationInput, ReservationResponse
from app.security import current_user

router = APIRouter(prefix="/reservations", tags=["reservations"])


@router.post("", response_model=ReservationResponse, status_code=201)
def create_reservation(payload: ReservationInput, username: str = Depends(current_user)):
    # Demonstration resource, not a booking in an external travel system.
    with connect() as session:
        resource = Reservation(owner=username, destination=payload.destination)
        session.add(resource)
        session.commit()
        session.refresh(resource)
        return ReservationResponse.model_validate(resource, from_attributes=True)


@router.get("/{reservation_id}", response_model=ReservationResponse)
def read_reservation(reservation_id: UUID, username: str = Depends(current_user)):
    with connect() as session:
        resource = session.exec(select(Reservation).where(
            Reservation.id == str(reservation_id), Reservation.owner == username)).first()
        if resource is None:
            raise HTTPException(404, "Reserva não encontrada")
        return ReservationResponse.model_validate(resource, from_attributes=True)
