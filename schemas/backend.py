from typing import List

from pydantic import BaseModel, Field


class Patient(BaseModel):
    hash: str = Field(default=None)
    age: str = Field(default=None)
    sex: str = Field(default=None)


class PayloadImage(BaseModel):
    id: str = Field(default=None)
    status: str = Field(default="pending")
    payload_id: str = Field(default="")
    s3_path: str = Field(default="")
    filename: str = Field(default="")
    device: str = Field(default="not stated")


class Payload(BaseModel):
    id: str = Field(default="")
    payload_stage: str = Field(default="before")
    payload_case: int = Field(default=1)
    status: str = Field(default="pending")
    patient: Patient = Field(default=Patient(hash="artificial", age="-1", sex="d"))
    images: List[PayloadImage] = Field(default=[])
    doctor: str = Field(default="artificial doctor")
    uploadtime: str = Field(default="-1 min")


class User(BaseModel):
    id: str
    username: str
    email: str
    realm_roles: list
    client_roles: list
