from fastapi import FastAPI

app = FastAPI(title="SellIA Sellbot", version="1.0.0")

@app.get("/test")
async def test():
    return {"status": "ok", "message": "app is running"}

@app.get("/api/health")
async def health():
    return {"status": "ok", "database": "pending"}
