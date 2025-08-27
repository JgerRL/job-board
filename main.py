from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Optional
from math import ceil

from db import fetch_jobs, list_sources

app = FastAPI(title="Niche Job Board")

# Static / Templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

DEFAULT_PER_PAGE = 20

@app.get("/", response_class=HTMLResponse)
def home(
    request: Request,
    page: int = Query(1, ge=1),
    q: Optional[str] = Query(None, description="Search keywords"),
    location: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    per_page: int = Query(DEFAULT_PER_PAGE, ge=5, le=100),
):
    rows, total = fetch_jobs(page=page, per_page=per_page, q=q, location=location, source=source)
    total_pages = max(1, ceil(total / per_page))

    # build pagination urls
    def page_url(p: int) -> str:
        params = []
        if q: params.append(f"q={q}")
        if location: params.append(f"location={location}")
        if source: params.append(f"source={source}")
        params.append(f"per_page={per_page}")
        params.append(f"page={p}")
        return "/?" + "&".join(params)

    context = {
        "request": request,
        "jobs": rows,
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
        "prev_url": page_url(page-1) if page > 1 else None,
        "next_url": page_url(page+1) if page < total_pages else None,
        "sources": list_sources(),
        "active": {"q": q or "", "location": location or "", "source": source or "", "per_page": per_page},
    }
    return templates.TemplateResponse("index.html", context)


@app.get("/api/jobs", response_class=JSONResponse)
def api_jobs(
    page: int = Query(1, ge=1),
    q: Optional[str] = None,
    location: Optional[str] = None,
    source: Optional[str] = None,
    per_page: int = Query(DEFAULT_PER_PAGE, ge=5, le=100),
):
    rows, total = fetch_jobs(page=page, per_page=per_page, q=q, location=location, source=source)
    return {
        "page": page,
        "per_page": per_page,
        "total": total,
        "jobs": [
            {
                "id": r["id"],
                "source": r["source"],
                "title": r["title"],
                "company": r["company"],
                "date": r["date"],
                "location": r["location"],
                "url": r["url"],
                "description": r["description"],
            }
            for r in rows
        ],
    }
