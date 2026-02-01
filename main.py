# PYTHON STANDARD IMPORTS
import os
import random
import json
from pathlib import Path
import shutil
from typing import Annotated
import requests 

# OTHER LIBARIES
from sqlmodel import Field, Session, SQLModel, create_engine, select 
from fastapi import FastAPI, Depends

# PROJECT FILES
from codes import *
import type as tp

# -- SETUP --

sqlite_file_name = "data/database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

app = FastAPI()

def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]

@app.on_event("startup")
async def start():
    SQLModel.metadata.create_all(engine)

pah = Path("Repos_config.json")
if not pah.exists():
    pah.write_text("{}")

with pah.open() as fp:
    Repos_config = json.load(fp)

# -- DataBase --

class User(SQLModel, table=True):
    usename: str = Field(primary_key=True)
    password: str = Field()
    cookie_id: int | None = Field(index=True, default=None)
    super_user: bool = Field(default=False)

class Author(SQLModel, table=True):
    name : str = Field(primary_key=True)
    banned : bool = Field()


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

def authenticate(cookie_id: str, session: SessionDep) -> bool:
    statement = select(User).where(User.cookie_id == cookie_id)
    return session.exec(statement).first() is not None


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/clear")
async def clear(req: tp.Basic, session: SessionDep):
    if not authenticate(req.cookie_id, session):
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


def find_author(name, session) -> Author | None:
    aut = session.get(Author, name)
    if aut:
        return aut
    else:
        return None
    
def create_author(name, session):
    aut = Author(name=name, banned=False)
    session.add(aut)
    session.commit()
    session.refresh(aut)

def fetch_commit_shas(repo, author):
    per_page = 100
    page = 1
    shas = []
    while True:
        url = f"https://api.github.com/repos/{author}/{repo}/commits"
        params = {
            "per_page": per_page,
            "page": page
        }

        res = requests.get(url, params=params)
        if res.status_code == 404:
            raise E404 (
                detail="Author / Repos Not found"
            )
        
        data = res.json()
        if not data: break
        for com in data:
            shas.append(com["sha"])
        page += 1
    return shas

def setup_config(repo, author):
    shas = fetch_commit_shas(repo, author)
    latest_sha = shas[0]
    _sentinel = object()

    value = Repos_config.get(latest_sha, _sentinel)

    if value is _sentinel:
        data = {
            "name": repo,
            "author": author,
            "installed": True
        }
        Repos_config[latest_sha] = data
    else:
        Repos_config[latest_sha]["installed"] = True
    


@app.post("/house/download/repo")
async def download_repo(req: tp.house_download, session: SessionDep):
    if not authenticate(req.cookie_id, session):
        raise E401(
            detail="User Not Signed In!"
        )
    author = find_author(req.author, session)
    if author == None:
        create_author(req.author, session)
    if author.banned == True: #type: ignore
        raise Forbidden(
            detail="Author Is Banned"
        )
    auth: Author = session.get(Author, author) # type: ignore
    if auth == None:
        return E404(
            detail="Author Not Found In database"
        )
    elif auth.banned == True:
        return Forbidden(
            detail="Author has been Banned"
        )
    else:
        item = f"https://github.com/{req.author}/{req.repo}"
        download_rep(item)
        return {"message": f"Downloading {item}"}

@app.post("/house/download/author")
async def download_author(req: tp.house_download, session: SessionDep):
    if not authenticate(req.cookie_id, session):
        raise E401(
            detail="User Not Signed In!"
        )
    author_name = req.author
    res = requests.get(f"https://api.github.com/users/{author_name}/repos")
    print(res.status_code)
    if res.status_code == 404:
        raise E404(
            detail="Author Not Found in github"
        )
    auth: Author = session.get(Author, author) # type: ignore
    if auth == None:
        return E404(
            detail="Author Not Found In database"
        )
    elif auth.banned == True:
        return Forbidden(
            detail="Author has been Banned"
        )
    else:
        data = res.json()
        for rep in data:
            print(f"Attempting to download: https://github.com/{rep['full_name']}")
            download_rep(f"https://github.com/{rep['full_name']}")

    return {}

def uninstall_repo_from_config(repo, author):
    shas = fetch_commit_shas(repo, author)
    latest_sha = shas[0]
    Repos_config[latest_sha]["installed"] = False

def uninstall_author_from_config(author):
    res = requests.get(f"https://api.github.com/users/{author}/repos")
    data = res.json()
    for repo in data:
        name = repo["name"]
        uninstall_repo_from_config(name, author)

@app.delete("/house/delete/author")
async def delete_author(req: tp.house_remove, session: SessionDep):
    if not authenticate(req.cookie_id, session):
        raise E401(
            detail="User Not Signed In!"
        )
    author_name = req.author
    p = Path(f"/home/aiden/safebox/house/{author_name}")
    if p.exists:
        uninstall_author_from_config(author_name)
        shutil.rmtree(str(p))
    else:
        raise E404(
            detail="Author Not Found"
        )
    return {}

@app.delete("/house/delete/repo")
async def delete_repo(req: tp.house_remove, session: SessionDep):
    if not authenticate(req.cookie_id, session):
        raise E401(
            detail="User Not Signed In!"
        )
    repo_name = req.repo
    author_name = req.author
    p = Path(f"/home/aiden/safebox/house/{author_name}/{repo_name}")
    if p.exists:
        uninstall_repo_from_config(repo_name, author_name)
        shutil.rmtree(str(p))
    else:
        raise E404(
            detail="Repo Not Found"
        )
    return {}

@app.get("/house/author/{author}")
async def return_author(author: str, session: SessionDep):
    auth: Author = session.get(Author, author) # type: ignore
    if auth == None:
        return E404(
            detail="Author Not Found"
        )
    else:
        return {
            "name" : auth.name,
            "banned": auth.banned
        }

@app.post("/house/config")
async def return_config():
    pass

@app.post("/house/ban/author")
async def ban_author(req: tp.house_ban, session: SessionDep):
    auth: Author = session.get(Author, author) # type: ignore
    if auth == None:
        return E404(
            detail="Author Not Found"
        )
    else:
        auth.banned = True
        session.add(auth)
        session.commit()

@app.post("/house/unban/author")
async def unban_author(req: tp.house_ban, session: SessionDep):
    auth: Author = session.get(Author, author) # type: ignore
    if auth == None:
        return E404(
            detail="Author Not Found"
        )
    else:
        auth.banned = False
        session.add(auth)
        session.commit()