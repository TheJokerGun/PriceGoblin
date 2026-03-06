from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import TrackingActiveUpdate, TrackingResponse
from ..services import auth_service, tracking_service

router = APIRouter(prefix="/api/tracking", tags=["Tracking"])


@router.get("", response_model=list[TrackingResponse])
def get_tracking(
    db: Session = Depends(get_db),
    current_user=Depends(auth_service.get_current_user),
) -> list[TrackingResponse]:
    return tracking_service.get_user_tracking(db, current_user.id)


@router.delete("/{tracking_id}")
def delete_tracking(
    tracking_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(auth_service.get_current_user),
) -> dict[str, str]:
    success = tracking_service.delete_tracking(db, current_user.id, tracking_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tracking entry not found")
    return {"detail": "Tracking entry deleted successfully"}


@router.patch("/{tracking_id}/active", response_model=TrackingResponse)
def update_tracking_active(
    tracking_id: int,
    payload: TrackingActiveUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(auth_service.get_current_user),
) -> TrackingResponse:
    tracking = tracking_service.update_tracking_active(
        db,
        current_user.id,
        tracking_id,
        payload.is_active,
    )
    if not tracking:
        raise HTTPException(status_code=404, detail="Tracking entry not found")
    return tracking
