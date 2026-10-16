from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.interview import router as interview_router
from app.api.curate import router as curate_router
from app.api.bluesky import router as bluesky_router
from app.api.feed import router as feed_router
from app.api.values import router as values_router



app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(interview_router)
app.include_router(curate_router)
app.include_router(bluesky_router)
app.include_router(feed_router)
app.include_router(values_router)

@app.get("/")
def root():
    return {"message": "Feed the Feed API is running"}


@app.get("/health")
def health():
    return {"status": "ok"}