import asyncio
import time
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database import get_session
from app.dependencies import get_current_user
from app.models.contract import Contract
from app.models.user import User
from app.services.llm import analyse_contract

router = APIRouter(prefix="/bulk", tags=["bulk"])


# ── Example 1: gather() — run multiple LLM calls concurrently ──────
@router.post("/analyse-all")
async def analyse_all_contracts(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Analyse ALL of the user's contracts at the same time.
    Without gather(): each analysis waits for the previous one.
    With gather(): all analyses run concurrently.
    """
    contracts = session.exec(
        select(Contract).where(Contract.owner_id == current_user.id)
    ).all()

    if not contracts:
        raise HTTPException(status_code=404, detail="No contracts found")

    if len(contracts) > 5:
        raise HTTPException(status_code=400, detail="Max 5 contracts at once")

    start = time.perf_counter()

    # gather() schedules all coroutines concurrently on the event loop.
    # If you had 3 contracts each taking 2 seconds:
    # Sequential: 6 seconds total
    # gather():   ~2 seconds total
    results = await asyncio.gather(
        *[analyse_contract(c.content) for c in contracts],
        return_exceptions=True  # don't cancel all if one fails
    )

    duration = round(time.perf_counter() - start, 2)

    output = []
    for contract, result in zip(contracts, results):
        if isinstance(result, Exception):
            output.append({
                "contract_id": contract.id,
                "title": contract.title,
                "error": str(result)
            })
        else:
            output.append({
                "contract_id": contract.id,
                "title": contract.title,
                "analysis": result
            })

    return {
        "total": len(contracts),
        "duration_seconds": duration,
        "results": output
    }


# ── Example 2: create_task() — fire and forget ─────────────────────
# A shared dict simulating a job store (use Redis in production)
background_jobs: dict[str, dict] = {}

async def run_analysis_in_background(job_id: str, content: str):
    """This runs independently — the HTTP response already returned."""
    try:
        background_jobs[job_id]["status"] = "running"
        result = await analyse_contract(content)
        background_jobs[job_id]["status"] = "done"
        background_jobs[job_id]["result"] = result
    except Exception as e:
        background_jobs[job_id]["status"] = "failed"
        background_jobs[job_id]["error"] = str(e)


@router.post("/analyse-async/{contract_id}")
async def start_async_analysis(
    contract_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Starts an analysis in the background and returns immediately.
    Poll /bulk/job/{job_id} to check status.
    This pattern is used for long-running tasks in production.
    """
    contract = session.get(Contract, contract_id)
    if not contract or contract.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Contract not found")

    job_id = f"job_{contract_id}_{int(time.time())}"
    background_jobs[job_id] = {"status": "queued", "contract_id": contract_id}

    # create_task() schedules the coroutine but doesn't wait for it.
    # The response returns immediately while the task runs in the background.
    asyncio.create_task(run_analysis_in_background(job_id, contract.content))

    return {
        "job_id": job_id,
        "status": "queued",
        "poll_url": f"/bulk/job/{job_id}"
    }


@router.get("/job/{job_id}")
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
):
    """Poll this to check if the background analysis is done."""
    job = background_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


# ── Example 3: write your own coroutine from scratch ───────────────
async def fetch_with_delay(label: str, delay: float) -> str:
    """A coroutine is just an async function. It can be awaited or gathered."""
    await asyncio.sleep(delay)  # non-blocking wait — event loop does other work
    return f"{label} done after {delay}s"


@router.get("/asyncio-demo")
async def asyncio_demo():
    """
    Demonstrates coroutines, gather, and the difference between
    sequential and concurrent execution.
    """
    # Sequential — total time = sum of all delays
    start = time.perf_counter()
    r1 = await fetch_with_delay("task-1", 0.5)
    r2 = await fetch_with_delay("task-2", 0.5)
    r3 = await fetch_with_delay("task-3", 0.5)
    sequential_time = round(time.perf_counter() - start, 3)

    # Concurrent with gather — total time = longest single delay
    start = time.perf_counter()
    results = await asyncio.gather(
        fetch_with_delay("task-1", 0.5),
        fetch_with_delay("task-2", 0.5),
        fetch_with_delay("task-3", 0.5),
    )
    concurrent_time = round(time.perf_counter() - start, 3)

    return {
        "sequential_seconds": sequential_time,   # ~1.5s
        "concurrent_seconds": concurrent_time,   # ~0.5s
        "speedup": f"{round(sequential_time / concurrent_time, 1)}x faster with gather()",
        "results": results
    }