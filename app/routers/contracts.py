from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.database import get_session
from app.dependencies import get_current_user
from app.models.contract import (
    Contract, ContractCreate, ContractPublic, ContractUpdate, ContractStatus
)
from app.models.user import User

router = APIRouter(prefix="/contracts", tags=["contracts"])


@router.post("/", response_model=ContractPublic)
def create_contract(
    contract_in: ContractCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    contract = Contract(**contract_in.model_dump(), owner_id=current_user.id)
    session.add(contract)
    session.commit()
    session.refresh(contract)
    return contract


@router.get("/", response_model=list[ContractPublic])
def list_contracts(
    status: ContractStatus | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    query = select(Contract).where(Contract.owner_id == current_user.id)
    if status:
        query = query.where(Contract.status == status)
    query = query.offset(skip).limit(limit)
    return session.exec(query).all()


@router.get("/{contract_id}", response_model=ContractPublic)
def get_contract(
    contract_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    contract = session.get(Contract, contract_id)
    if not contract or contract.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Contract not found")
    return contract


@router.patch("/{contract_id}", response_model=ContractPublic)
def update_contract(
    contract_id: int,
    updates: ContractUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    contract = session.get(Contract, contract_id)
    if not contract or contract.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Contract not found")

    update_data = updates.model_dump(exclude_unset=True)  # only update provided fields
    for key, value in update_data.items():
        setattr(contract, key, value)

    session.add(contract)
    session.commit()
    session.refresh(contract)
    return contract


@router.delete("/{contract_id}", status_code=204)
def delete_contract(
    contract_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    contract = session.get(Contract, contract_id)
    if not contract or contract.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Contract not found")
    session.delete(contract)
    session.commit()