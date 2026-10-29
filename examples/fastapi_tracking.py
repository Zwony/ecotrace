"""
FastAPI example demonstrating EcoTrace emissions tracking.

Install dependencies:
    pip install -e ".[web]"
    pip install fastapi uvicorn

Run from the repository root:
    uvicorn examples.fastapi_tracking:app --reload

Or run from the examples directory:
    cd examples
    uvicorn fastapi_tracking:app --reload

Try:
    GET http://127.0.0.1:8000/health
    GET http://127.0.0.1:8000/compute

Inspect the response headers:
    X-Eco-Carbon-Emitted
    X-Eco-Duration
"""

from fastapi import FastAPI

from ecotrace.middleware.fastapi import EcoTraceMiddleware


app = FastAPI(title="EcoTrace FastAPI Example")

# EcoTrace measures requests and adds emissions and duration headers.
app.add_middleware(EcoTraceMiddleware)


@app.get("/health")
async def health():
    """Lightweight endpoint for checking application health."""
    return {"status": "ok"}


@app.get("/compute")
def compute():
    """Perform CPU-intensive work to demonstrate request tracking."""
    total = sum(number * number for number in range(1_000_000))

    return {
        "status": "completed",
        "result": total,
    }