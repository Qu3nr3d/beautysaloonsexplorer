"""
Warsaw Hair/Beauty Salon Data Collector v4
- Overpass: bbox Warszawy
- Yelp: filtr tylko Warszawa po mieście i współrzędnych
- Dzielnice: geometrycznie (błyskawiczne, bez Nominatim)
"""

import csv
import json
import os
import time
import logging
import re
from dataclasses import dataclass, asdict
from math import radians, sin, cos, sqrt, atan2
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

OUTPUT_CSV  = "data/salons.csv"
OUTPUT_JSON = "data/salons.json"

YELP_API_KEY = os.environ.get("YELP_API_KEY", "")

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (compatible; salon-collector/1.0)",
    "Accept-Language": "pl-PL,pl;q=0.9",
})

# ---------------------------------------------------------------------------
# Granice Warszawy (bounding box + filtr współrzędnych)
# ---------------------------------------------------------------------------

WARSAW_BBOX = (52.09, 20.85, 52.37, 21.27)   # (min_lat, min_lon, max_lat, max_lon)
WARSAW_NAMES = {"warsaw", "warszawa"}


def in_warsaw_bbox(lat: float, lon: float) -> bool:
    min_lat, min_lon, max_lat, max_lon = WARSAW_BBOX
    return min_lat <= lat <= max_lat and min_lon <= lon <= max_lon


# ---------------------------------------------------------------------------
# Dzielnice Warszawy — geometryczne przypisanie (Voronoi po centroidach)
# ---------------------------------------------------------------------------

DISTRICTS = [
    ("Śródmieście",    52.2297, 21.0122),
    ("Mokotów",        52.1910, 21.0230),
    ("Praga-Południe", 52.2400, 21.0730),
    ("Ursynów",        52.1500, 21.0500),
    ("Wola",           52.2330, 20.9700),
    ("Bielany",        52.2900, 20.9600),
    ("Żoliborz",       52.2700, 20.9900),
    ("Bemowo",         52.2500, 20.9100),
    ("Ochota",         52.2150, 20.9800),
    ("Targówek",       52.2800, 21.0700),
    ("Białołęka",      52.3300, 21.0600),
    ("Praga-Północ",   52.2540, 21.0600),
    ("Wilanów",        52.1650, 21.0900),
    ("Ursus",          52.2000, 20.8900),
    ("Włochy",         52.1950, 20.9300),
    ("Wawer",          52.2100, 21.1400),
    ("Rembertów",      52.2600, 21.1600),
    ("Wesoła",         52.2500, 21.2200),
]


def _dist_km(lat1, lon1, lat2, lon2) -> float:
    R = 6371
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)
    a = sin(d_lat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))


def assign_district(lat: float, lon: float) -> str:
    if not lat or not lon:
        return ""
    best, best_d = "", 999.0
    for name, dlat, dlon in DISTRICTS:
        d = _dist_km(lat, lon, dlat, dlon)
        if d < best_d:
            best, best_d = name, d
    return best


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Salon:
    name:         str   = ""
    address:      str   = ""
    district:     str   = ""
    phone:        str   = ""
    website:      str   = ""
    services:     str   = ""
    price_range:  str   = ""
    rating:       str   = ""
    review_count: str   = ""
    lat:          float = 0.0
    lon:          float = 0.0
    source:       str   = ""

# ---------------------------------------------------------------------------
# Part 1 — Overpass (GET, fallback serwery)
# ---------------------------------------------------------------------------

OVERPASS_SERVERS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]

OVERPASS_QUERY = """
[out:json][timeout:60];
(
  nwr["shop"="hairdresser"](52.09,20.85,52.37,21.27);
  nwr["shop"="beauty"](52.09,20.85,52.37,21.27);
  nwr["amenity"="beauty_salon"](52.09,20.85,52.37,21.27);
);
out center tags;
"""

DISTRICT_TAGS = ["addr:suburb", "addr:city_district", "is_in:suburb", "addr:quarter"]


def _extract_district_tag(tags: dict) -> str:
    for key in DISTRICT_TAGS:
        if tags.get(key):
            return tags[key]
    return ""


def _build_address(tags: dict) -> str:
    street   = tags.get("addr:street", "")
    number   = tags.get("addr:housenumber", "")
    postcode = tags.get("addr:postcode", "")
    city     = tags.get("addr:city", "Warszawa")
    parts    = [f"{street} {number}".strip(), postcode, city]
    return ", ".join(p for p in parts if p)


def fetch_overpass() -> list[Salon]:
    log.info("Fetching from Overpass API (GET) ...")
    encoded = requests.utils.quote(OVERPASS_QUERY)

    for server in OVERPASS_SERVERS:
        url = f"{server}?data={encoded}"
        try:
            resp = SESSION.get(url, timeout=90)
            if resp.status_code != 200:
                log.warning("  %s -> HTTP %d, próbuję następny", server, resp.status_code)
                continue
        except requests.RequestException as e:
            log.warning("  %s -> błąd: %s", server, e)
            continue

        elements = resp.json().get("elements", [])
        log.info("  Overpass zwrócił %d elementów", len(elements))

        salons = []
        for el in elements:
            tags = el.get("tags", {})
            name = tags.get("name", "").strip()
            if not name:
                continue
            lat = float(el.get("lat") or el.get("center", {}).get("lat") or 0)
            lon = float(el.get("lon") or el.get("center", {}).get("lon") or 0)

            # Tylko Warszawa
            if not in_warsaw_bbox(lat, lon):
                continue

            district = _extract_district_tag(tags) or assign_district(lat, lon)

            salons.append(Salon(
                name     = name,
                address  = _build_address(tags),
                district = district,
                phone    = tags.get("phone", tags.get("contact:phone", "")),
                website  = tags.get("website", tags.get("contact:website",
                            tags.get("contact:facebook", ""))),
                lat      = lat,
                lon      = lon,
                source   = "overpass",
            ))

        log.info("  -> %d salonów z Overpass (w granicach Warszawy)", len(salons))
        return salons

    log.error("Wszystkie serwery Overpass niedostępne")
    return []


# ---------------------------------------------------------------------------
# Part 2 — Yelp (tylko Warszawa)
# ---------------------------------------------------------------------------

YELP_SEARCH_URL = "https://api.yelp.com/v3/businesses/search"
YELP_CATEGORIES = ["hair", "beautysvc", "barbers", "nailedsalons", "skincare", "makeupartists"]
YELP_PRICE_MAP  = {"$": "do 50 PLN", "$$": "50–150 PLN", "$$$": "150–300 PLN", "$$$$": "300+ PLN"}


def fetch_yelp() -> list[Salon]:
    if not YELP_API_KEY:
        log.warning("Brak YELP_API_KEY – pomijam Yelp.")
        return []

    headers = {"Authorization": f"Bearer {YELP_API_KEY}"}
    salons: list[Salon] = []
    skipped = 0

    for category in YELP_CATEGORIES:
        log.info("  Yelp – kategoria: %s", category)
        offset = 0

        while offset < 1000:
            params = {
                "location":   "Warszawa, Polska",
                "categories": category,
                "limit":      50,
                "offset":     offset,
                "locale":     "pl_PL",
                # Środek Warszawy + promień 15km (Yelp i tak może wychodzić poza)
                "latitude":   52.2297,
                "longitude":  21.0122,
                "radius":     15000,
            }
            try:
                resp = SESSION.get(YELP_SEARCH_URL, headers=headers, params=params, timeout=30)
                if resp.status_code == 429:
                    log.warning("    Rate limit – czekam 60s")
                    time.sleep(60)
                    continue
                resp.raise_for_status()
                data = resp.json()
            except requests.RequestException as e:
                log.warning("    Yelp błąd (offset=%d): %s", offset, e)
                break

            businesses = data.get("businesses", [])
            if not businesses:
                break

            for b in businesses:
                coords = b.get("coordinates", {})
                lat = float(coords.get("latitude",  0) or 0)
                lon = float(coords.get("longitude", 0) or 0)

                # Twardy filtr: tylko w granicach Warszawy
                if lat and lon and not in_warsaw_bbox(lat, lon):
                    skipped += 1
                    continue

                loc  = b.get("location", {})
                city = loc.get("city", "")
                # Filtr po nazwie miasta jeśli brak koordynatów
                if not lat and city.lower() not in WARSAW_NAMES:
                    skipped += 1
                    continue

                addr = ", ".join(filter(None, [
                    loc.get("address1", ""),
                    loc.get("zip_code", ""),
                    loc.get("city", ""),
                ]))

                district = assign_district(lat, lon) if lat else ""

                categories_str = ", ".join(c.get("title", "") for c in b.get("categories", []))
                price_raw      = b.get("price", "")
                price_range    = YELP_PRICE_MAP.get(price_raw, price_raw)

                salons.append(Salon(
                    name         = b.get("name", "").strip(),
                    address      = addr,
                    district     = district,
                    phone        = b.get("phone", ""),
                    website      = b.get("url", ""),
                    services     = categories_str,
                    price_range  = price_range,
                    rating       = str(b.get("rating", "")),
                    review_count = str(b.get("review_count", "")),
                    lat          = lat,
                    lon          = lon,
                    source       = f"yelp:{category}",
                ))

            offset += len(businesses)
            if len(businesses) < 50 or offset >= data.get("total", 0):
                break
            time.sleep(0.3)

        log.info("    Yelp łącznie: %d (pominięto poza Warszawą: %d)", len(salons), skipped)

    log.info("  -> %d salonów z Yelp", len(salons))
    return salons


# ---------------------------------------------------------------------------
# Part 3 — Merge & deduplicate
# ---------------------------------------------------------------------------

def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.lower().strip())


def merge(overpass: list[Salon], yelp: list[Salon]) -> list[Salon]:
    merged: dict[str, Salon] = {}

    for s in overpass:
        key = _norm(s.name) + "|" + _norm(s.address.split(",")[0])
        merged[key] = s

    for y in yelp:
        key = _norm(y.name) + "|" + _norm(y.address.split(",")[0])
        if key in merged:
            e = merged[key]
            if y.rating:                      e.rating       = y.rating
            if y.review_count:                e.review_count = y.review_count
            if y.services:                    e.services     = y.services
            if y.price_range:                 e.price_range  = y.price_range
            if y.district and not e.district: e.district     = y.district
            if y.phone and not e.phone:       e.phone        = y.phone
            if y.website and not e.website:   e.website      = y.website
            e.source += "+yelp"
        else:
            merged[key] = y

    result = list(merged.values())
    log.info("Po merge & dedup: %d unikalnych salonów", len(result))
    return result


# ---------------------------------------------------------------------------
# Part 4 — Save
# ---------------------------------------------------------------------------

FIELDNAMES = [
    "name", "address", "district",
    "phone", "website",
    "services", "price_range",
    "rating", "review_count",
    "lat", "lon", "source",
]


def save(salons: list[Salon]) -> None:
    os.makedirs("data", exist_ok=True)
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for s in salons:
            writer.writerow({k: getattr(s, k) for k in FIELDNAMES})
    log.info("Zapisano CSV  -> %s", OUTPUT_CSV)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump([asdict(s) for s in salons], f, ensure_ascii=False, indent=2)
    log.info("Zapisano JSON -> %s", OUTPUT_JSON)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    osm_salons  = fetch_overpass()
    yelp_salons = fetch_yelp()

    all_salons = merge(osm_salons, yelp_salons)
    all_salons.sort(key=lambda s: (s.district.lower(), s.name.lower()))

    # Tylko kompletne rekordy
    all_salons = [
        s for s in all_salons
        if s.name and s.address and s.district
        and s.phone and s.services
        and s.rating and s.rating != "0"
    ]
    log.info("Po filtrze kompletności: %d salonów", len(all_salons))

    save(all_salons)

    print(f"\n{'='*50}")
    print(f"  Łącznie unikalnych salonów : {len(all_salons)}")
    print(f"  Z oceną                    : {sum(1 for s in all_salons if s.rating and s.rating != '0')}")
    print(f"  Z telefonem                : {sum(1 for s in all_salons if s.phone)}")
    print(f"  Z usługami                 : {sum(1 for s in all_salons if s.services)}")
    print(f"  Z przedziałem cenowym      : {sum(1 for s in all_salons if s.price_range)}")
    print(f"  Z dzielnicą                : {sum(1 for s in all_salons if s.district)}")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()