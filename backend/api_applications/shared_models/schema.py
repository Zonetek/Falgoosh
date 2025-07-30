from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime


class FingerPrintInfo(BaseModel):
    os_match: Optional[str] = None
    os_family: Optional[str] = None
    accuracy: Optional[str] = None
    type: Optional[str] = None
    os_Gen: Optional[str] = None
    vendor: Optional[str] = None


class GeoInfo(BaseModel):
    country: Optional[str]
    city: Optional[str]
    regionname: Optional[str]
    latlang: Optional[list]


class GeneralInfo(BaseModel):
    geo: Optional[GeoInfo]
    isp: Optional[str]
    organization: Optional[str]
    asn: Optional[str]


class VulnerabilityInfo(BaseModel):
    cv_id: str
    description: str
    published: str
    assigner: str


class ScanResult(BaseModel):
    id: str = Field(alias="_id")
    ports: List[int]
    last_update: datetime
    finger_print: Optional[FingerPrintInfo] = None
    general: Optional[GeneralInfo] = None
    domain: Optional[str] = None
    service_type: Optional[Dict[int, str]] = None  # port(int): str
    vulnerability: Optional[Dict[str, List[VulnerabilityInfo]]] = (
        None  # sercicename(str) : list (contains dict ---> cv_id : VulnerabilityInfo model  )
    )

    class Config:
        allow_population_by_field_name = True
        populate_by_name = True
