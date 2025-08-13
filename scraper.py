import requests
import feedparser
import sqlite3
import time
from bs4 import BeautifulSoup
from flask import Flask, jsonify
from log_wrapper import LogWrapper 

logger = LogWrapper(name="job_scraper").logger

DB_NAME = "jobs.sqlite"
KEYWORDS = ["junior", "entry", "graduate", "intern", "trainee", "associate", "apprentice", "new grad", "new graduate", "fresh graduate", "fresh grad", "recent graduate"]

def matches_keywords(text):
    return any(k in text.lower() for k in KEYWORDS)

def exclude_keywords(text):
    exclude = ["senior", "lead", "manager", "director", "architect", "vp", "executive", "principal", "experienced", "expert", "Sr."]
    return not any(k in text.lower() for k in exclude)

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT,
        title TEXT,
        company TEXT,
        date TEXT,
        location TEXT,
        url TEXT UNIQUE,
        description TEXT
    )""")
    conn.commit()
    conn.close()

def save_job(job):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO jobs (source, title, company, date, location, url, description) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (job["source"], job["title"], job["company"], job["date"], job["location"], job["url"], job["description"]))
        conn.commit()
        logger.info(f"Saved job: {job['title']} at {job['company']} ({job['source']})")
    except sqlite3.IntegrityError:
        logger.debug(f"Duplicate job skipped: {job['title']} ({job['source']})")
    conn.close()

def scrape_remoteok():
    logger.info("Scraping RemoteOK...")
    time.sleep(2)
    jobs = []
    try:
        response = requests.get("https://remoteok.com/api", headers={"User-Agent": "Mozilla/5.0"})
        if response.ok:
            for job in response.json()[1:]:
                if matches_keywords(job.get("position", "")) or exclude_keywords(job.get("position", "")):
                    jobs.append({
                        "source": "RemoteOK",
                        "title": job["position"],
                        "company": job["company"],
                        "date": job["date"],
                        "location": job.get("location", "Remote"),
                        "url": job["url"],
                        "description": job.get("description", "")[:200] + "..."
                    })
        logger.info(f"RemoteOK found {len(jobs)} matching jobs.")
    except Exception as e:
        logger.error(f"Error scraping RemoteOK: {e}")
    return jobs

def scrape_weworkremotely():
    logger.info("Scraping WeWorkRemotely...")
    time.sleep(2)
    jobs = []
    try:
        feed = feedparser.parse("https://weworkremotely.com/categories/remote-programming-jobs.rss")
        for entry in feed.entries:
            if matches_keywords(entry.title) or exclude_keywords(entry.title):
                jobs.append({
                    "source": "WeWorkRemotely",
                    "title": entry.title,
                    "company": entry.title.split("–")[0].strip() if "–" in entry.title else "Unknown",
                    "date": entry.published,
                    "location": "Remote",
                    "url": entry.link,
                    "description": entry.summary[:200] + "..."
                })
        logger.info(f"WeWorkRemotely found {len(jobs)} matching jobs.")
    except Exception as e:
        logger.error(f"Error scraping WeWorkRemotely: {e}")
    return jobs

def run_scrapers():
    logger.info("Starting scrapers...")
    init_db()
    for scraper in (scrape_remoteok, scrape_weworkremotely):
        for job in scraper():
            save_job(job)
    logger.info("Scraping complete.")

app = Flask(__name__)

@app.route("/jobs")
def get_jobs():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM jobs ORDER BY date DESC")
    jobs = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(jobs)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "scrape":
        run_scrapers()
    else:
        app.run(debug=True, host="0.0.0.0", port=5000)
