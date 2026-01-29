from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import os
from hashlib import sha256
import type as tp
from typing import Annotated
import requests 
from pathlib import Path
import shutil
from sqlmodel import Field, Session, SQLModel, create_engine, select 
import random
from codes import *

sqlite_file_name = "data/database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

app = FastAPI()

def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]

class User(SQLModel, table=True): # type: ignore
    usename: str = Field(primary_key=True)
    password: str = Field()
    cookie_id: int | None = Field(index=True, default=None)

class request(BaseModel):
    target_link: str | None = None

@app.on_event("startup")
async def start():
    SQLModel.metadata.create_all(engine)

@app.post("/winter/login")
async def login(req: tp.login_request, session: SessionDep):
    name = req.username
    pw = req.password
    us: User = session.get(User, name) # type: ignore
    if us.cookie_id != None:
        return {"Cookie": us.cookie_id}
    elif pw == us.password:
        us.cookie_id = random.randint(0, 100000000)
        session.add(us)
        session.commit()
        return {"Cookie": us.cookie_id}

    return {}

@app.post("/winter/register")
async def register(req: tp.register_request, session: SessionDep):
    name = req.username
    pw = req.password
    us = User(usename=name, password=pw)
    session.add(us)
    session.commit()
    session.refresh(us)

    return {}

def authenticate(cookie_id, session: Annotated) -> bool:
    statement = select(User).where(User.cookie_id == cookie_id)
    item = session.exec(statement).first()
    if item:
        return True
    return False

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/clear")
async def clear(req: tp.Basic):
    if not authenticate(req.cookie_id, SessionDep):
        raise E401(
            detail="User Not Signed In!"
        )
    os.system("rm -rf house")
    os.system("mkdir house")
    return {"message": "Clearing the house"}

def download_rep(link: str):
    name = link[18 : len(link)]
    print(f"Name: {name}")
    p = Path(f"/home/aiden/safebox/house{name}")
    if not p.exists:
        print(f"Path: /home/aiden/safebox/house{name} Exists")
    else:
        os.system(f"git clone {link} house/{name}")


@app.post("/house/download/repo")
async def download_repo(req: tp.house_download):
    if not authenticate(req.cookie_id, SessionDep):
        raise E401(
            detail="User Not Signed In!"
        )
    item = f"https://github.com/{req.author}/{req.repo}"
    download_rep(item)
    return {"message": f"Downloading {item}"}

@app.post("/house/download/author")
async def download_author(req: tp.house_download):
    if not authenticate(req.cookie_id, SessionDep):
        raise E401(
            detail="User Not Signed In!"
        )
    author_name = req.author
    res = requests.get(f"https://api.github.com/users/{author_name}/repos")
    if res.status_code == 404:
        raise E404(
            detail="Author Not Found"
        )
    else:
        data = res.json()
        for rep in data:
            print(f"Attempting to download: https://github.com/{rep['full_name']}")
            download_rep(f"https://github.com/{rep['full_name']}")

    return {}

@app.delete("/house/delete/author")
async def delete_author(req: tp.house_remove):
    if not authenticate(req.cookie_id, SessionDep):
        raise E401(
            detail="User Not Signed In!"
        )
    author_name = req.author
    p = Path(f"/home/aiden/safebox/house/{author_name}")
    if p.exists:
        shutil.rmtree(str(p))
    else:
        raise E404(
            detail="Author Not Found"
        )
    return {}

@app.delete("/house/delete/repo")
async def delete_repo(req: tp.house_remove):
    if not authenticate(req.cookie_id, SessionDep):
        raise E401(
            detail="User Not Signed In!"
        )
    repo_name = req.repo
    author_name = req.author
    p = Path(f"/home/aiden/safebox/house/{author_name}/{repo_name}")
    if p.exists:
        shutil.rmtree(str(p))
    else:
        raise E404(
            detail="Repo Not Found"
        )
    return {}


