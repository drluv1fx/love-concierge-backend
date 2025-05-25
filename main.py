
# main.py (placeholder - replace with your actual backend code)
from fastapi import FastAPI
app = FastAPI()

@app.get("/")
def read_root():
    return {"msg": "Hello from Love Concierge Backend"}
