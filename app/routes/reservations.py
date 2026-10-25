from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from app.database import Reservation, connect
from app.models import ReservationInput, ReservationResponse
from app.security import current_user

router = APIRouter(prefix="/reservations", tags=["reservations"])


@router.post("", response_model=ReservationResponse, status_code=201,
             summary="Criar reserva local de laboratório",
             description="Armazena somente destino e owner do token; não efetua compra. Owner/status no body são rejeitados.",
             responses={401: {"description": "Bearer ausente ou inválido"}, 422: {"description": "Entrada inválida ou campo extra"}})
def create_reservation(payload: ReservationInput, username: str = Depends(current_user)):
    # Demonstration resource, not a booking in an external travel system.
    with connect() as session:
        resource = Reservation(owner=username, destination=payload.destination)
        session.add(resource)
        session.commit()
        session.refresh(resource)
        return ReservationResponse.model_validate(resource, from_attributes=True)


@router.get("/{reservation_id}", response_model=ReservationResponse,
            summary="Consultar somente a própria reserva",
            description="Consulta conjunta por UUID e owner autenticado. Outro usuário e ID inexistente recebem o mesmo 404.",
            responses={401: {"description": "Bearer ausente ou inválido"}, 404: {"description": "Reserva não encontrada para este usuário"}})
def read_reservation(reservation_id: UUID, username: str = Depends(current_user)):
    with connect() as session:
        resource = session.exec(select(Reservation).where(
            Reservation.id == str(reservation_id), Reservation.owner == username)).first()
        if resource is None:
            raise HTTPException(404, "Reserva não encontrada")
        return ReservationResponse.model_validate(resource, from_attributes=True)
