from database import SessionLocal
from models import Salon

KEEP_KEYWORDS = {
    'hair', 'hairdresser', 'fryzjer', 'fryzjersk', 'strzyżen', 'strzyzen',
    'farbowanie', 'keratyna', 'balayage', 'highlight',
    'beauty', 'salon kosmetyczn', 'kosmetyczn', 'kosmetolog',
    'nail', 'paznokcie', 'manicure', 'pedicure',
    'barber', 'barbershop', 'golenie',
    'skin', 'skincare', 'twarz', 'peeeling', 'peeling', 'oczyszczanie',
    'lash', 'rzęsy', 'rzesy', 'brwi', 'brow',
    'makeup', 'makijaż', 'makijaz',
    'wax', 'depilacja', 'sugaring',
    'spa', 'masaż', 'masaz', 'relaks',
    'solarium', 'opalanie',
}

BAD_KEYWORDS = {
    'pub', 'puby', 'bar ', 'bary', 'kawiarni', 'restaur', 'kuchnia',
    'tajska', 'tajski', 'meksykańska', 'meksykanska', 'włoska', 'wloska',
    'grecka', 'francuska', 'azjatycka', 'chińska', 'chinska',
    'pizza', 'burger', 'sushi', 'tacos', 'pączki', 'paczki',
    'ciastka', 'piekarni', 'cukierni', 'śniadanie', 'sniadanie', 'brunch',
    'wine', 'koktajl', 'piwo', 'craft beer',
}


def should_keep(salon: Salon) -> bool:
    text = ((salon.services or '') + ' ' + (salon.name or '')).lower()
    if any(bw in text for bw in BAD_KEYWORDS):
        return False
    return any(kw in text for kw in KEEP_KEYWORDS)

def cleanup():
    db = SessionLocal()
    try:
        candidates = db.query(Salon).filter(Salon.source.like('%beautysvc%')).all()
        to_delete = [s for s in candidates if not should_keep(s)]

        print(f"Sprawdzono: {len(candidates)} rekordów yelp:beautysvc")
        print(f"Do usunięcia: {len(to_delete)}\n")
        for s in to_delete:
            print(f"  [{s.id}] {s.name} | {s.services}")

        if not to_delete:
            print("Nic do usunięcia.")
            return

        ans = input(f"\nUsunąć {len(to_delete)} rekordów? [t/N] ")
        if ans.lower() == 't':
            for s in to_delete:
                db.delete(s)
            db.commit()
            print(f"Usunięto {len(to_delete)}. Pozostało w bazie: {db.query(Salon).count()}")
        else:
            print("Anulowano.")
    finally:
        db.close()


if __name__ == "__main__":
    cleanup()