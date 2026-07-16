from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    code: int
    message: str
    data: T


class RootData(BaseModel):
    name: str
    status: str


class HealthData(BaseModel):
    status: str
