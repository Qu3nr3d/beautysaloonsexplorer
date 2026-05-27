from fastapi import FastAPI, HTTPException, Depends, Query, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional

import models
import crud
import schemas
from database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Warsaw Beauty Salons API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/")
def index(
    request: Request,
    district: Optional[str] = Query(None),
    service:  Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    salons = crud.get_salons(db, district=district, service=service, limit=500)
    districts = crud.get_all_districts(db)
    return templates.TemplateResponse(request, "index.html", {
        "salons": salons,
        "districts": districts,
        "selected_district": district or "",
        "selected_service": service or "",
        "total": len(salons),
    })


@app.get("/salons/{salon_id}")
def detail(request: Request, salon_id: int, db: Session = Depends(get_db)):
    salon = crud.get_salon(db, salon_id)
    if not salon:
        raise HTTPException(status_code=404, detail="Salon nie znaleziony")
    return templates.TemplateResponse(request, "detail.html", {"salon": salon})


@app.get("/salons/{salon_id}/edit")
def edit_form(request: Request, salon_id: int, db: Session = Depends(get_db)):
    salon = crud.get_salon(db, salon_id)
    if not salon:
        raise HTTPException(status_code=404, detail="Salon nie znaleziony")
    return templates.TemplateResponse(request, "edit.html", {"salon": salon})


@app.post("/salons/{salon_id}/edit")
def edit_submit(
    salon_id:    int,
    db:          Session = Depends(get_db),
    name:        str = Form(...),
    address:     str = Form(...),
    district:    str = Form(...),
    phone:       str = Form(""),
    website:     str = Form(""),
    services:    str = Form(""),
    price_range: str = Form(""),
    rating:      str = Form(""),
):
    data = schemas.SalonUpdate(
        name=name, address=address, district=district,
        phone=phone, website=website, services=services,
        price_range=price_range, rating=rating,
    )
    salon = crud.update_salon(db, salon_id, data)
    if not salon:
        raise HTTPException(status_code=404, detail="Salon nie znaleziony")
    return RedirectResponse(url=f"/salons/{salon_id}", status_code=303)

@app.get("/api/salons", response_model=list[schemas.SalonListItem])
def api_list_salons(
    district: Optional[str] = Query(None),
    service:  Optional[str] = Query(None),
    skip:     int           = Query(0, ge=0),
    limit:    int           = Query(100, ge=1, le=500),
    db:       Session       = Depends(get_db),
):
    return crud.get_salons(db, district=district, service=service, skip=skip, limit=limit)


@app.get("/api/salons/{salon_id}", response_model=schemas.SalonResponse)
def api_get_salon(salon_id: int, db: Session = Depends(get_db)):
    salon = crud.get_salon(db, salon_id)
    if not salon:
        raise HTTPException(status_code=404, detail="Salon nie znaleziony")
    return salon


@app.patch("/api/salons/{salon_id}", response_model=schemas.SalonResponse)
def api_update_salon(salon_id: int, data: schemas.SalonUpdate, db: Session = Depends(get_db)):
    salon = crud.update_salon(db, salon_id, data)
    if not salon:
        raise HTTPException(status_code=404, detail="Salon nie znaleziony")
    return salon