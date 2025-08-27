# job-board

# To get started
python -m venv venv && pip install -r requirements.txt
# Activate venv
source venv/bin/activate

# To run the scraper and the frontend
python scraper.py
uvicorn main:app --reload