import sqlite3
from typing import List, Tuple, Optional, Dict, Any

DB_NAME = "jobs.sqlite"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def build_filters(q: Optional[str], location: Optional[str], source: Optional[str]) -> Tuple[str, List[Any]]:
    clauses = []
    params: List[Any] = []

    if q:
        clauses.append("(title LIKE ? OR company LIKE ? OR description LIKE ?)")
        like = f"%{q}%"
        params.extend([like, like, like])

    if location:
        clauses.append("location LIKE ?")
        params.append(f"%{location}%")

    if source:
        clauses.append("source = ?")
        params.append(source)

    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    return where, params

def fetch_jobs(
    page: int = 1,
    per_page: int = 20,
    q: Optional[str] = None,
    location: Optional[str] = None,
    source: Optional[str] = None,
) -> Tuple[List[sqlite3.Row], int]:
    """
    Returns (rows, total_count)
    Uses your existing schema: columns -> id, source, title, company, date, location, url, description
    """
    offset = (page - 1) * per_page
    where, params = build_filters(q, location, source)

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(f"SELECT COUNT(*) FROM jobs{where}", params)
        total = cur.fetchone()[0]

        cur.execute(
            f"""
            SELECT id, source, title, company, date, location, url, description
            FROM jobs
            {where}
            ORDER BY date DESC
            LIMIT ? OFFSET ?
            """,
            params + [per_page, offset],
        )
        rows = cur.fetchall()

    return rows, total

def list_sources() -> List[str]:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT source FROM jobs ORDER BY source ASC")
        return [r[0] for r in cur.fetchall()]
