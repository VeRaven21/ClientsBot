from pydantic import BaseModel

import uuid

from typing import List


class ServiceSchema(BaseModel):
    id: uuid.UUID
    name: str
    price: int


class ServicesResponse(BaseModel):
    services: List[ServiceSchema]
    count: int
