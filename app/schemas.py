from pydantic import BaseModel
from typing import Optional

class CustomerSchema(BaseModel):
    first_name: str
    last_name: str
    phone_number: str

class GlobalGameStateSchema(BaseModel):
    state = str = "1,1,4,6,4,5,2,3,2,3,5,6"
    global_best = int = 0