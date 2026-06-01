from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.database import get_session
from app.dependencies import get_current_user
from app.models.contract import Contract
from app.models.user import User
from app.services.llm import analyse_contract

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/{contract_id}")
async def analyse(
    contract_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    contract = session.get(Contract, contract_id)
    if not contract or contract.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Contract not found")

    try:
        result = await analyse_contract(contract.content)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM analysis failed: {str(e)}")

    return {"contract_id": contract_id, "analysis": result}