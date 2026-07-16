from pydantic import BaseModel


class CurrentUser(BaseModel):
    id: str
    username: str
