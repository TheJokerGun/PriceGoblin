from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.backend.routes.scraper import router as scrape_router

app = FastAPI()

# Development CORS: allow same-network access and preflight requests
app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

app.include_router(scrape_router)
