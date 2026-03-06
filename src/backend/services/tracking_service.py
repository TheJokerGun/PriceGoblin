from sqlalchemy.orm import Session

from ..models import Tracking


def get_user_tracking(db: Session, user_id: int) -> list[Tracking]:
    return (
        db.query(Tracking)
        .filter(Tracking.user_id == user_id)
        .order_by(Tracking.created_at.desc(), Tracking.id.desc())
        .all()
    )


def get_tracking_by_id(db: Session, user_id: int, tracking_id: int) -> Tracking | None:
    return (
        db.query(Tracking)
        .filter(
            Tracking.id == tracking_id,
            Tracking.user_id == user_id,
        )
        .first()
    )


def delete_tracking(db: Session, user_id: int, tracking_id: int) -> bool:
    tracking = get_tracking_by_id(db, user_id, tracking_id)
    if not tracking:
        return False

    db.delete(tracking)
    db.commit()
    return True


def update_tracking_active(
    db: Session,
    user_id: int,
    tracking_id: int,
    is_active: bool | None = None,
) -> Tracking | None:
    tracking = get_tracking_by_id(db, user_id, tracking_id)
    if not tracking:
        return None

    tracking.is_active = (not tracking.is_active) if is_active is None else is_active
    db.add(tracking)
    db.commit()
    db.refresh(tracking)
    return tracking
