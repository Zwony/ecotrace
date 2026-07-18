"""EcoTrace hosted dashboard API.

Dashboard data is only sourced from measurements sent by a user's own
EcoTrace process to ``POST /api/metrics/ingest``; it never fabricates data.
"""
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field
from starlette.middleware.sessions import SessionMiddleware

from auth import (create_access_token, create_user, database, get_current_user_from_token,
                  initialize_database, oauth, oauth2_scheme, register_or_login_oauth_user,
                  user_from_ingestion_key, verify_password)
from config import settings
from database import Measurement, User
from sqlalchemy import select


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.environment.lower() == "production" and settings.jwt_secret_key == "change-me-before-production":
        raise RuntimeError("JWT_SECRET_KEY must be set in production")
    initialize_database()
    yield


app = FastAPI(title="EcoTrace Dashboard API", version="2.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=False,
                   allow_methods=["GET", "POST"], allow_headers=["Authorization", "Content-Type", "X-EcoTrace-Key"])
app.add_middleware(SessionMiddleware, secret_key=settings.jwt_secret_key, https_only=settings.environment.lower() == "production", same_site="lax")


class SignUpRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserProfileResponse(BaseModel):
    email: str
    name: str
    created_at: float


class IngestionKeyResponse(BaseModel):
    ingestion_key: str


class MeasurementIn(BaseModel):
    function: str = Field(min_length=1, max_length=250)
    carbon_gco2: float = Field(ge=0, le=1_000_000)
    duration_s: float = Field(ge=0, le=86_400)
    region: Optional[str] = Field(default=None, max_length=32)
    run_id: Optional[str] = Field(default=None, max_length=128)
    run_label: Optional[str] = Field(default=None, max_length=128)
    recorded_at: Optional[float] = None


class FunctionEmissions(BaseModel):
    name: str
    carbon: float
    duration: float
    status: str


class MetricsResponse(BaseModel):
    total_carbon: float
    active_sessions: int
    functions_count: int
    carbon_budget: float
    latest_point: float
    delta: float
    chart_points: List[float]
    functions: List[FunctionEmissions]


@app.post("/api/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(body: SignUpRequest):
    email = str(body.email).lower()
    with database() as db:
        existing = db.get(User, email)
    if existing:
        raise HTTPException(status_code=409, detail="An account with this email address already exists.")
    create_user(email, body.name.strip(), password=body.password)
    return {"access_token": create_access_token({"sub": email, "name": body.name.strip()})}


@app.post("/api/token", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    with database() as db:
        user = db.get(User, form_data.username.lower())
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect email or password.")
    return {"access_token": create_access_token({"sub": user.email, "name": user.name})}


@app.get("/api/me", response_model=UserProfileResponse)
async def get_me(token: str = Depends(oauth2_scheme)):
    user = get_current_user_from_token(token)
    return {"email": user["email"], "name": user["name"], "created_at": user["created_at"]}


@app.post("/api/ingestion-key", response_model=IngestionKeyResponse)
async def rotate_ingestion_key(token: str = Depends(oauth2_scheme)):
    """Issue a replacement key for sending this account's EcoTrace measurements."""
    from auth import hash_ingestion_key, new_ingestion_key
    user = get_current_user_from_token(token)
    key = new_ingestion_key()
    with database() as db:
        account = db.get(User, user["email"])
        account.api_key_hash = hash_ingestion_key(key)
    return {"ingestion_key": key}


@app.post("/api/metrics/ingest", status_code=status.HTTP_202_ACCEPTED)
async def ingest_measurement(body: MeasurementIn, request: Request):
    user = user_from_ingestion_key(request.headers.get("X-EcoTrace-Key", ""))
    recorded_at = body.recorded_at if body.recorded_at else time.time()
    if recorded_at > time.time() + 300:
        raise HTTPException(status_code=422, detail="recorded_at cannot be more than five minutes in the future")
    with database() as db:
        db.add(Measurement(user_email=user["email"], recorded_at=recorded_at, function_name=body.function,
                           carbon_gco2=body.carbon_gco2, duration_s=body.duration_s, region=body.region,
                           run_id=body.run_id, run_label=body.run_label))
    return {"accepted": True}


@app.get("/api/metrics", response_model=MetricsResponse)
async def get_metrics(token: str = Depends(oauth2_scheme)):
    user = get_current_user_from_token(token)
    with database() as db:
        rows = db.scalars(select(Measurement).where(Measurement.user_email == user["email"])
                          .order_by(Measurement.recorded_at.desc()).limit(5000)).all()
    rows = list(reversed(rows))
    total = sum(row.carbon_gco2 for row in rows)
    by_function = defaultdict(lambda: [0.0, 0.0])
    for row in rows:
        by_function[row.function_name][0] += row.carbon_gco2
        by_function[row.function_name][1] += row.duration_s
    functions = []
    for name, (carbon, duration) in by_function.items():
        functions.append(FunctionEmissions(name=name, carbon=carbon, duration=duration,
                         status="err" if carbon > 0.6 else "warn" if carbon > 0.2 else "ok"))
    functions.sort(key=lambda item: item.carbon, reverse=True)
    now = time.time()
    buckets = defaultdict(float)
    for row in rows:
        bucket = int(row.recorded_at // 2) * 2
        if bucket >= now - 60:
            buckets[bucket] += row.carbon_gco2
    chart = [buckets.get(int(now // 2) * 2 - 2 * offset, 0.0) for offset in range(29, -1, -1)]
    latest, previous = chart[-1], chart[-2]
    active_runs = {row.run_id for row in rows if row.run_id and row.recorded_at >= now - 300}
    return MetricsResponse(total_carbon=total, active_sessions=len(active_runs), functions_count=len(functions),
                           carbon_budget=5.0, latest_point=latest, delta=latest - previous,
                           chart_points=chart, functions=functions[:50])


def oauth_redirect(token: str) -> RedirectResponse:
    # Fragment keeps the token out of web-server logs and referrer headers.
    return RedirectResponse(url=f"{settings.frontend_url.rstrip('/')}/dashboard.html#token={token}")


@app.get("/login/google")
async def login_google(request: Request):
    if not settings.google_oauth_configured:
        raise HTTPException(status_code=503, detail="Google OAuth is not configured on this deployment.")
    return await oauth.google.authorize_redirect(request, request.url_for("auth_google"))


@app.get("/auth/google/callback")
async def auth_google(request: Request):
    token = await oauth.google.authorize_access_token(request)
    info = token.get("userinfo") or (await oauth.google.get("https://openidconnect.googleapis.com/v1/userinfo", token=token)).json()
    if not info.get("email") or not info.get("email_verified", False):
        raise HTTPException(status_code=400, detail="Google did not provide a verified email address.")
    return oauth_redirect(register_or_login_oauth_user(info["email"], info.get("name") or info["email"].split("@")[0], "google"))


@app.get("/login/github")
async def login_github(request: Request):
    if not settings.github_oauth_configured:
        raise HTTPException(status_code=503, detail="GitHub OAuth is not configured on this deployment.")
    return await oauth.github.authorize_redirect(request, request.url_for("auth_github"))


@app.get("/auth/github/callback")
async def auth_github(request: Request):
    token = await oauth.github.authorize_access_token(request)
    profile = (await oauth.github.get("user", token=token)).json()
    emails = (await oauth.github.get("user/emails", token=token)).json()
    primary = next((entry for entry in emails if entry.get("primary") and entry.get("verified")), None)
    if not primary:
        raise HTTPException(status_code=400, detail="GitHub did not provide a verified primary email address.")
    return oauth_redirect(register_or_login_oauth_user(primary["email"], profile.get("name") or profile.get("login") or primary["email"].split("@")[0], "github"))


LANDING_DIR = Path(__file__).resolve().parent.parent / "landing"
app.mount("/landing", StaticFiles(directory=LANDING_DIR, html=True), name="landing")


@app.get("/")
async def redirect_root_to_landing():
    return RedirectResponse(url="/landing/index.html")
