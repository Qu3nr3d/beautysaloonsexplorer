# Warsaw Beauty Salons

A database of hair salons and beauty parlors in Warsaw with a web interface and REST API.

## Requirements

- Python 3.11+
- Yelp Fusion API key ([register here](https://www.yelp.com/developers/v3/manage_app))

## How to Run the Application

```bash
git clone https://github.com/Qu3nr3d/beautysaloonsexplorer beautysalooons
cd beautysalooons

python -m venv .venv
.venv\Scripts\activate        # Windows

pip install -r requirements.txt
```

Set your Yelp API key and collect data:

```bash
$env:YELP_API_KEY="your_key"     # Windows PowerShell

python app/collect_overpass.py
```

Load the database and start the server:

```bash
cd app
python seed.py
uvicorn main:app --reload
```

App available at [http://127.0.0.1:8000](http://127.0.0.1:8000)

API docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Technical Solution

**Data sources**
- [OpenStreetMap Overpass API](https://overpass-api.de/) — free, no key required; provides name, address, district, phone, and website for salons within Warsaw's bounding box
- [Yelp Fusion API](https://www.yelp.com/developers) — free tier (500 req/day); enriches records with ratings, review counts, services, and price range
- Records from both sources are merged and deduplicated by name + address; districts are assigned geometrically using centroids of Warsaw's 18 districts

**Backend**
- [FastAPI](https://fastapi.tiangolo.com/) — REST API and server-side rendered pages
- [SQLAlchemy](https://www.sqlalchemy.org/) — ORM with SQLite database
- [Pydantic](https://docs.pydantic.dev/) — request/response validation
- [Jinja2](https://jinja.palletsprojects.com/) — HTML templating

**Frontend**
- Plain HTML + CSS (no framework)
- Filtering by district (dropdown) and service (text search)
- Detail page and edit form for each salon

## API Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| `GET` | `/` | Main page — salon listing |
| `GET` | `/salons/{id}` | Salon detail page |
| `GET` | `/salons/{id}/edit` | Edit form |
| `POST` | `/salons/{id}/edit` | Submit edit form |
| `GET` | `/api/salons` | List all salons |
| `GET` | `/api/salons?district=Mokotów` | Filter by district |
| `GET` | `/api/salons?service=manicure` | Filter by service |
| `GET` | `/api/salons/{id}` | Salon details |
| `PATCH` | `/api/salons/{id}` | Update salon |

## Project Structure

```
beautysalooons/
├── app/
│   ├── static/
│   │   └── style.css
│   ├── templates/
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── detail.html
│   │   └── edit.html
│   ├── collect_overpass.py     # data collection from Overpass & Yelp
│   ├── cleanup.py        # remove invalid records
│   ├── seed.py           # load CSV into database
│   ├── main.py           # FastAPI routes
│   ├── crud.py           # database operations
│   ├── models.py         # SQLAlchemy model
│   ├── schemas.py        # Pydantic schemas
│   └── database.py       # database configuration
├── data/
│   └── salons.csv        # collected data
├── requirements.txt
└── README.md
```

## What I'd Improve with More Time

- **User roles** — separate admin and regular user accounts; only admins would be able to edit or delete salon records, while regular users could browse and filter
- **Better data quality** — the current Yelp `beautysvc` category occasionally includes restaurants and cafes; a more robust ML-based or rule-based classifier would filter these out automatically during collection rather than requiring manual cleanup
- **Pagination** — the listing currently loads up to 500 records at once; proper server-side pagination with page controls would improve performance
- **Search** — full-text search across name, address, and services instead of simple substring filtering
- **Map view** — an interactive map showing salon locations using the stored lat/lon coordinates
- **User reviews** — allow users to add their own ratings and comments on top of the imported Yelp data
- **Automatic data refresh** — a scheduled job (e.g. cron or Celery) to re-collect and update salon data periodically instead of running the script manually
- **Deployment** — containerize with Docker and deploy to a cloud provider with a proper PostgreSQL database instead of SQLite