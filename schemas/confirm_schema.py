from pydantic import BaseModel
from typing import Literal
from app.constants.workflow_status import ConfirmationAction


class ConfirmRequest(BaseModel):
    workflow_id: str
    confirmation_id: str

    action: ConfirmationAction
