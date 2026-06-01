from datetime import datetime
from typing import Any
from fastapi import APIRouter
from pydantic import BaseModel, field_validator, computed_field

router = APIRouter(prefix="/demo", tags=["serialization-demo"])


# ── Nested models ───────────────────────────────────────────────────
class Address(BaseModel):
    street: str
    city: str
    country: str = "India"


class ContactInfo(BaseModel):
    phone: str
    address: Address  # nested model — Pydantic handles this automatically


class CompanyProfile(BaseModel):
    name: str
    founded_year: int
    contact: ContactInfo  # doubly nested

    @computed_field  # computed at serialization time, not stored
    @property
    def age_years(self) -> int:
        return datetime.now().year - self.founded_year


@router.get("/nested-models")
def nested_models_demo():
    """
    Build a deeply nested model and serialise it different ways.
    """
    profile = CompanyProfile(
        name="Acme Corp",
        founded_year=2018,
        contact=ContactInfo(
            phone="+91-9876543210",
            address=Address(
                street="42 MG Road",
                city="Bangalore",
            )
        )
    )

    return {
        # model_dump() — Python dict (datetime objects stay as datetime)
        "as_dict": profile.model_dump(),

        # model_dump(mode='json') — JSON-safe dict (datetime → ISO string)
        # Use this before json.dumps() or when returning to non-Pydantic code
        "as_json_safe": profile.model_dump(mode="json"),

        # exclude fields
        "without_contact": profile.model_dump(exclude={"contact"}),

        # include only specific fields
        "name_only": profile.model_dump(include={"name", "age_years"}),

        # nested exclusion — exclude city from address
        "no_city": profile.model_dump(exclude={"contact": {"address": {"city"}}}),
    }


# ── model_validate() — parsing from dict/JSON ──────────────────────
@router.post("/parse-from-dict")
def parse_from_dict_demo(raw_data: dict[str, Any]):
    """
    model_validate() is how you build a Pydantic model from a raw dict.
    This is what FastAPI does internally with your request body.
    Use it yourself when you get data from a DB, an external API, or a file.
    """
    try:
        profile = CompanyProfile.model_validate(raw_data)
        return {
            "parsed_successfully": True,
            "name": profile.name,
            "age_years": profile.age_years,
            "city": profile.contact.address.city,
        }
    except Exception as e:
        return {"parsed_successfully": False, "error": str(e)}


# ── model_dump with aliases and by_alias ───────────────────────────
class APIResponse(BaseModel):
    """Some external APIs expect camelCase. Pydantic handles the translation."""
    contract_id: int
    risk_level: str
    created_at: datetime

    model_config = {"populate_by_name": True}


@router.get("/serialization-modes")
def serialization_modes_demo():
    response = APIResponse(
        contract_id=42,
        risk_level="medium",
        created_at=datetime.now()
    )
    return {
        # Default — snake_case, datetime as datetime object
        "default": response.model_dump(),

        # JSON mode — all types become JSON-serializable
        # datetime → "2025-01-01T12:00:00"
        "json_mode": response.model_dump(mode="json"),

        # JSON string — full serialization to a string
        "as_json_string": response.model_dump_json(),
    }