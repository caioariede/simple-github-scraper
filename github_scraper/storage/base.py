from typing import List

from ..models import User, Repo


class Q:
    """ Q function allows building basic queries using a pythonic approach
    """
    LT = '<'
    GT = '>'

    def __init__(self, name, op=None, value=None):
        self.name = name
        self.op = op
        self.value = value

    def __gt__(self, value):
        return Q(self.name, self.GT, value)

    def __lt__(self, value):
        return Q(self.name, self.LT, value)


class Storage:
    """ Base Storage class with interface methods
    """
    def close(self):
        raise NotImplementedError  # pragma: no cover

    def __enter__(self):
        raise NotImplementedError  # pragma: no cover

    def __exit__(self, *args):
        raise NotImplementedError  # pragma: no cover

    def put_user(self, obj: User):
        """ Insert or update user
        """
        raise NotImplementedError  # pragma: no cover

    def get_user(self, **lookup) -> User:
        """ Returns first user matching lookup
        """
        raise NotImplementedError  # pragma: no cover

    def get_last_user(self) -> User:
        """ Return last user in storage
        """
        raise NotImplementedError  # pragma: no cover

    def list_users(self,
                   order_by=None,
                   offset=None,
                   limit=None,
                   **lookup) -> List[User]:
        """ Returns filtered list of users
        """
        raise NotImplementedError  # pragma: no cover

    def put_repo(self, obj: Repo):
        """ Insert or update repo
        """
        raise NotImplementedError  # pragma: no cover

    def get_repo(self, **lookup) -> Repo:
        """ Returns first repo matching lookup
        """
        raise NotImplementedError  # pragma: no cover

    def list_repos(self,
                   order_by=None,
                   offset=None,
                   limit=None,
                   **lookup) -> List[Repo]:
        """ Returns filtered list of repos
        """
        raise NotImplementedError  # pragma: no cover
