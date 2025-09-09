# Weather-Data-Aggregation-Service
Weather Data Aggregation Service from different providers

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
