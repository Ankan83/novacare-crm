from datetime import datetime

from pydantic import BaseModel, ConfigDict # type: ignore


class HCPBase(BaseModel):
    full_name: str
    specialty: str
    organization: str
    city: str
    email: str
    notes: str = ""


class HCPResponse(HCPBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)