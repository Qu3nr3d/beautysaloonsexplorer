# Warsaw Beauty Salons

A database of hair salons and beauty parlors in Warsaw with a web interface and REST API.

## Requirements

- Python 3.11+
- Yelp Fusion API key ([register here](https://www.yelp.com/developers/v3/manage_app))

## Installation

```bash
git clone https://github.com/your-user/beautysalooons.git
cd beautysalooons

python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac

pip install -r requirements.txt
```

## Collecting Data

```bash
$env:YELP_API_KEY="your_key"     # Windows PowerShell
# export YELP_API_KEY="your_key" # Linux/Mac

python app/collect_v4.py
```

Data will be saved to `data/salons.csv`.

## Seeding the Database

```bash
cd app
python seed.py
```

## Running the App

```bash
cd app
uvicorn main:app --reload
```

App available at [http://127.0.0.1:8000](http://127.0.0.1:8000)

API docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

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
│   ├── cleanup.py              # remove invalid records
│   ├── seed.py                 # load CSV into database
│   ├── main.py                 # FastAPI routes
│   ├── crud.py                 # database operations
│   ├── models.py               # SQLAlchemy model
│   ├── schemas.py              # Pydantic schemas
│   └── database.py             # database configuration
├── data/
│   └── salons.csv        # collected data
├── requirements.txt
└── README.md
```

## API Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| `GET` | `/api/salons` | List all salons |
| `GET` | `/api/salons?district=Mokotów` | Filter by district |
| `GET` | `/api/salons?service=manicure` | Filter by service |
| `GET` | `/api/salons/{id}` | Salon details |
| `PATCH` | `/api/salons/{id}` | Update salon |