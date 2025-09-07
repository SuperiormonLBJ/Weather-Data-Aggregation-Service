# Weather-Data-Aggregation-Service
Weather Data Aggregation Service from different providers

# Folder structure
weather-api/
├─ app/
│  ├─ main.py          # FastAPI app entrypoint
│  ├─ routes.py        # API endpoints (/weather)
│  ├─ services.py      # business logic (fetch + aggregate providers)
│  ├─ providers/       # one file per weather provider
│  │   ├─ openweather.py
│  │   ├─ weatherapi.py
│  │   └─ openmeteo.py
│  └─ schemas.py       # request/response Pydantic models
├─ tests/              # unit tests (later)
├─ requirements.txt    # dependencies
└─ README.md

### Create virutal env
python -m venv weather-env

### Activate virtual environment
#### On macOS/Linux:
source venv/bin/activate
#### On Windows:
venv\Scripts\activate

### Install dependencies
pip install -r requirements.txt

### Setup .env file for API keys and other project level configuration

### Run this python fastAPI project
uvicorn app.main:app --reload
