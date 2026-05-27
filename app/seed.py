import csv
from database import engine, SessionLocal
import models

models.Base.metadata.create_all(bind=engine)


def seed():
    db = SessionLocal()
    try:
        existing = db.query(models.Salon).count()
        if existing > 0:
            print(f"Baza już zawiera {existing} salonów — pomijam seed.")
            return

        with open("data/salons.csv", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            salons = []
            for row in reader:
                salons.append(models.Salon(
                    name         = row.get("name", ""),
                    address      = row.get("address", ""),
                    district     = row.get("district", ""),
                    phone        = row.get("phone", ""),
                    website      = row.get("website", ""),
                    services     = row.get("services", ""),
                    price_range  = row.get("price_range", ""),
                    rating       = row.get("rating", ""),
                    review_count = row.get("review_count", ""),
                    lat          = float(row.get("lat") or 0),
                    lon          = float(row.get("lon") or 0),
                    source       = row.get("source", ""),
                ))

        db.bulk_save_objects(salons)
        db.commit()
        print(f"Dodano {len(salons)} salonów do bazy.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()