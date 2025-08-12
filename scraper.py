import requests
import feedparser
import sqlite3
import time
from flask import Flask, jsonify

DB_NAME = "jobs.sqlite"

# =========================
# Database Setup
# =========================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            title TEXT,
            company TEXT,
            date_posted TEXT,
            location TEXT,
            url TEXT UNIQUE,
            description TEXT
        )
    """)
    conn.commit()
    conn.close()

# =========================
# Save Job (Avoid Duplicates)
# =========================
def save_job(job):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO jobs (source, title, company, date_posted, location, url, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            job["source"], job["title"], job["company"],
            job["date"], job["location"], job["url"], job["description"]
        ))
        conn.commit()
    except sqlite3.IntegrityError:
        # URL already exists (duplicate)
        print(f"Duplicate job found: {job['url']}, skipping.")
        pass
    finally:
        conn.close()

# =========================
# Scraper Functions
# =========================
def scrape_remoteok():
    print("Scraping RemoteOK...")
    url = "https://remoteok.com/api"
    headers = {"User-Agent": "Mozilla/5.0"}
    time.sleep(2)  # polite delay
    response = requests.get(url, headers=headers)
    jobs = []

    if response.status_code == 200:
        data = response.json()[1:]  # first item is metadata
        for job in data:
            if "junior" in job["position"].lower():
                jobs.append({
                    "source": "RemoteOK",
                    "title": job["position"],
                    "company": job["company"],
                    "date": job["date"],
                    "location": job.get("location", "Remote"),
                    "url": job["url"],
                    "description": job.get("description", "")[:200] + "..."
                })
    return jobs

def scrape_weworkremotely():
    print("Scraping WeWorkRemotely...")
    url = "https://weworkremotely.com/categories/remote-programming-jobs.rss"
    time.sleep(2)  # polite delay
    feed = feedparser.parse(url)
    jobs = []

    for entry in feed.entries:
        if "junior" in entry.title.lower():
            jobs.append({
                "source": "WeWorkRemotely",
                "title": entry.title,
                "company": entry.title.split("–")[0].strip() if "–" in entry.title else "Unknown",
                "date": entry.published,
                "location": "Remote",
                "url": entry.link,
                "description": entry.summary[:200] + "..."
            })
    return jobs

# =========================
# Run Scrapers
# =========================
def run_scrapers():
    init_db()
    sources = [scrape_remoteok, scrape_weworkremotely]
    for scrape_func in sources:
        jobs = scrape_func()
        for job in jobs:
            save_job(job)
    print("Scraping complete.")

# =========================
# Flask API
# =========================
app = Flask(__name__)

@app.route("/jobs", methods=["GET"])
def get_jobs():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT source, title, company, date_posted, location, url, description FROM jobs ORDER BY date_posted DESC")
    rows = cursor.fetchall()
    conn.close()

    jobs = []
    for row in rows:
        jobs.append({
            "source": row[0],
            "title": row[1],
            "company": row[2],
            "date": row[3],
            "location": row[4],
            "url": row[5],
            "description": row[6]
        })
    return jsonify(jobs)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "scrape":
        run_scrapers()
    else:
        app.run(debug=True, host="0.0.0.0", port=5000)
