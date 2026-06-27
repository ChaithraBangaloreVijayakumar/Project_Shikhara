# Project Shikhara 🛕

> *A shikhara (शिखर) is the towering spire that crowns a Hindu temple — a vertical axis connecting earth to the divine, and the most recognisable silhouette of temple architecture across the Indian subcontinent. Project Shikhara takes its name from this structure: a guiding landmark, visible from afar, helping people find their way.*

**Project Shikhara** is a public web directory of Hindu temples across Germany — an open, searchable, and interactive resource for the Hindu diaspora and the culturally curious.

---

## What it does

- 🗺️ **Interactive map** — browse temples across Germany on a Leaflet-powered map, filterable by state
- 🔍 **Temple detail pages** — opening hours, contact details, location, and social media links for each temple
- 🤖 **AI-powered chatbot** — ask natural language questions like *"Which temples are open on Sundays in NRW?"* or *"Is there a Ganesha temple near Frankfurt?"*

---

## Why it exists

Germany is home to a growing Hindu diaspora, yet there is no single, reliable, publicly accessible directory of Hindu temples in the country. Information is scattered across community WhatsApp groups, outdated PDFs, and individual temple websites — if they exist at all.

This project aims to change that: one place, all temples, always up to date.

---

## Tech stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python) |
| Frontend | HTML / CSS / Vanilla JavaScript |
| Map | Leaflet.js |
| Database | PostgreSQL + pgvector |
| AI / RAG | LangChain + Groq (LLaMA 3) |
| Data pipeline | Python (pandas) |
| CI/CD | GitHub Actions |
| Hosting | Render / Streamlit Cloud |

---

## Data pipeline

Raw temple data was assembled from a combination of Google Maps scraping and manual research — OpenStreetMap alone covers only ~25% of Hindu temples in Germany, making multi-source curation essential.

```
raw_data.csv
    └── clean_data.py        # Cleans, standardises, and transforms raw data
         └── transformed_data.csv
              └── load_data.py     # Loads into PostgreSQL with upsert support
                   └── PostgreSQL  # location + temples + temple_contact + temple_hours
```

Key cleaning steps:
- Filtering invalid and unverified entries
- Phone numbers normalised to `+49 XXX XXXXXXX` format, stored as JSON lists
- Opening hours parsed from free text into structured 24-hour JSON format
- URLs normalised to `https://` and stored as JSON lists
- Postal codes preserved as strings (leading zeros retained)
- UTF-8 BOM handling for Windows compatibility

### Database schema

```
location          (postal_code PK, state)
temples           (id PK, name, street, city, postal_code FK, lat, lon, note)
temple_contact    (id PK, temple_id FK, contact_type ENUM, value)
temple_hours      (id PK, temple_id FK, day ENUM, hours)
```

The `location` table maps all 8,273 German postal codes to their Bundesland, sourced from [moralescastillo/datasets](https://github.com/moralescastillo/datasets). This enables state-level grouping across the website without relying on inconsistent city name matching.

---

## Project structure

```
Project_Shikhara/
├── data/
│   ├── raw/                  # Raw input CSVs
│   ├── scripts/              # Data pipeline scripts
│   │   ├── clean_data.py
│   │   └── load_data.py
│   └── transformed/          # Cleaned output CSVs
├── database/
│   ├── schema.sql            # Table definitions, ENUMs, indexes, triggers
│   └── migrate.sql           # One-time migration to normalised schema
├── backend/                  # FastAPI application (coming soon)
├── frontend/                 # JS/Leaflet frontend (coming soon)
├── chatbot/                  # RAG pipeline and LangChain agent (coming soon)
├── .env                      # Local environment variables (never committed)
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Getting started

### Prerequisites
- Python 3.11+
- PostgreSQL 18+
- pip

### Setup

```bash
# Clone the repository
git clone https://github.com/<your-username>/Project_Shikhara.git
cd Project_Shikhara

# Install dependencies
pip install -r requirements.txt

# Create your .env file
cp .env.example .env
# Fill in your PostgreSQL credentials

# Set up the database
psql -U postgres -d shikhara -f database/schema.sql

# Run the data pipeline
python data/scripts/clean_data.py data/raw/raw_data.csv data/transformed/transformed_data.csv
python data/scripts/load_data.py data/transformed/transformed_data.csv
```

---

## Status

| Component | Status |
|---|---|
| Data collection & cleaning | ✅ Complete |
| Database schema & loading | ✅ Complete |
| FastAPI backend | 🔄 In progress |
| Leaflet frontend | ⏳ Planned |
| RAG chatbot | ⏳ Planned |
| CI/CD & deployment | ⏳ Planned |

---

## About

Built by [Chaithra](https://github.com/<your-username>) as a portfolio project combining data engineering, full-stack web development, and applied AI — with the goal of building something genuinely useful for a real community.
