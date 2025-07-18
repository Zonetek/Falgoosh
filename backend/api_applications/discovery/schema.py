from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime


class ScanResult(BaseModel):
    id: str = Field(alias="_id")
    ports: List[int]
    last_update: datetime
    finger_print: Optional[Dict] = None
    general: Optional[Dict] = None
    domain: Optional[str] = None
    service_type: Optional[Dict] = None
    vulnerability: Optional[Dict] = None

    class Config:
        allow_population_by_field_name = True
