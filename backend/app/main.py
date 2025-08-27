from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS（Next.js開発用。必要に応じて調整）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # or "http://127.0.0.1:3000"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}
