from pydantic import BaseModel

class login_request(BaseModel):
    pass

class register_request(BaseModel):
    pass

class house_download(BaseModel):
    author: str | None = None
    repo: str | None = None

class house_remove(house_download):
    pass