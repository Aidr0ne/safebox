from pydantic import BaseModel

class Basic(BaseModel):
    cookie_id:str

class register_request(BaseModel):
    username: str
    password: str

class login_request(register_request):
    pass

class house_download(Basic):
    author: str | None = None
    repo: str | None = None

class house_remove(house_download):
    pass
