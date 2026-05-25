from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional

import models
import crud
import schemas
from database import engine, get_db

# Tworzy tabele jeśli nie istnieją
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Warsaw Beauty Salons API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# GET /salons — lista salonów (name, district, rating, price_range)
# ---------------------------------------------------------------------------

@app.get("/salons", response_model=list[schemas.SalonListItem])
def list_salons(
    district: Optional[str] = Query(None, description="Filtruj po dzielnicy"),
    service:  Optional[str] = Query(None, description="Filtruj po usłudze"),
    skip:     int           = Query(0,    ge=0),
    limit:    int           = Query(100,  ge=1, le=500),
    db:       Session       = Depends(get_db),
):
    return crud.get_salons(db, district=district, service=service, skip=skip, limit=limit)


# ---------------------------------------------------------------------------
# GET /salons/{id} — pełne szczegóły salonu
# ---------------------------------------------------------------------------

@app.get("/salons/{salon_id}", response_model=schemas.SalonResponse)
def get_salon(salon_id: int, db: Session = Depends(get_db)):
    salon = crud.get_salon(db, salon_id)
    if not salon:
        raise HTTPException(status_code=404, detail="Salon nie znaleziony")
    return salon


# ---------------------------------------------------------------------------
# PATCH /salons/{id} — modyfikacja danych salonu
# ---------------------------------------------------------------------------

@app.patch("/salons/{salon_id}", response_model=schemas.SalonResponse)
def update_salon(salon_id: int, data: schemas.SalonUpdate, db: Session = Depends(get_db)):
    salon = crud.update_salon(db, salon_id, data)
    if not salon:
        raise HTTPException(status_code=404, detail="Salon nie znaleziony")
    return salon