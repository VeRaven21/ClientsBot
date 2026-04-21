from pydantic import BaseModel


class Client(BaseModel):
    id: int
    username: str
    full_name: str
