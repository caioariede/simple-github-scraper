from typing import NamedTuple


class User(NamedTuple):
    id: int
    login: str
    user_url: str


class Repo(NamedTuple):
    id: int
    user_id: int
    repo_url: str
    name: str
    description: str
    language: str
