from sqlalchemy.orm import Session
from models import Salon
from schemas import SalonUpdate


def get_salons(
    db: Session,
    district: str | None = None,
    service:  str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Salon]:
    q = db.query(Salon)
    if district:
        q = q.filter(Salon.district.ilike(f"%{district}%"))
    if service:
        q = q.filter(Salon.services.ilike(f"%{service}%"))
    return q.offset(skip).limit(limit).all()


def get_salon(db: Session, salon_id: int) -> Salon | None:
    return db.query(Salon).filter(Salon.id == salon_id).first()


def get_all_districts(db: Session) -> list[str]:
    rows = db.query(Salon.district).distinct().order_by(Salon.district).all()
    return [r[0] for r in rows if r[0]]


def update_salon(db: Session, salon_id: int, data: SalonUpdate) -> Salon | None:
    salon = get_salon(db, salon_id)
    if not salon:
        return None
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(salon, field, value)
    db.commit()
    db.refresh(salon)
    return salon