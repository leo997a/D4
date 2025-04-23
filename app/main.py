from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .scraper import scrape_whoscored
import asyncio

app = FastAPI()

class MatchUrl(BaseModel):
    url: str

@app.post("/scrape")
async def scrape_match(data: MatchUrl):
    if not data.url.startswith("https://www.whoscored.com/"):
        raise HTTPException(status_code=400, detail="Invalid WhoScored URL")

    result = await scrape_whoscored(data.url)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    return result

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
