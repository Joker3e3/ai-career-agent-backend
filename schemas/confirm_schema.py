from pydantic import BaseModel
from typing import Literal


class ConfirmRequest(BaseModel):
    workflow_id: str
    confirmation_id: str

    action: Literal["approve", "revise", "reject"]
