from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect

from app.api.routers import admin_entries, admin_users, auth, entries, media, tests
from app.core.config import get_settings
from app.core.database import Base, SessionLocal, engine
from app.models import AppSetting, Entry, Example, TestAttempt, User  # noqa: F401
from app.services.auth_service import AuthService
from app.services.media_settings_service import MediaSettingsService


@asynccontextmanager
async def lifespan(_app: FastAPI):
    expected_tables = set(Base.metadata.tables.keys())
    existing_tables = set(inspect(engine).get_table_names())
    missing_tables = sorted(expected_tables - existing_tables)
    if missing_tables:
        print(f"[startup] Missing tables detected: {', '.join(missing_tables)}. Creating...")
    else:
        print("[startup] All expected tables already exist.")

    Base.metadata.create_all(bind=engine)
    settings = get_settings()
    db = SessionLocal()
    try:
        AuthService(db).seed_admin_if_empty(settings.seed_admin_username, settings.seed_admin_password)
        MediaSettingsService.seed_defaults(db)
    finally:
        db.close()
    yield


app = FastAPI(title="Japanese Speaking Drill API", lifespan=lifespan)
settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(entries.router)
app.include_router(tests.router)
app.include_router(media.router)
app.include_router(admin_users.router)
app.include_router(admin_entries.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
