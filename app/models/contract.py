from datetime import datetime
from enum import Enum
from sqlmodel import SQLModel, Field


class ContractStatus(str, Enum):
    draft = "draft"
    active = "active"
    expired = "expired"


class ContractBase(SQLModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=10)
    status: ContractStatus = ContractStatus.draft
    effective_date: datetime | None = None


class Contract(ContractBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    owner_id: int = Field(foreign_key="user.id")


class ContractCreate(ContractBase):
    pass


class ContractPublic(ContractBase):
    id: int
    created_at: datetime
    owner_id: int


class ContractUpdate(SQLModel):
    title: str | None = None
    content: str | None = None
    status: ContractStatus | None = None
    effective_date: datetime | None = None