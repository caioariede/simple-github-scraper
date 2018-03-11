from . import Storage, Q
from ..models import User, Repo

from typing import List, Tuple

import sqlite3


class SQLiteStorage(Storage):
    """ SQLite Storage

    :param database: database path
    """
    def __init__(self, database: str):
        self.conn = sqlite3.connect(database)
        self.closed = False
        self.create_tables()

    def close(self):
        self.conn.close()
        self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def create_tables(self):
        c = self.conn.cursor()
        c.execute('''
CREATE TABLE IF NOT EXISTS user (
    id          integer     primary key,
    login       text,
    user_url    text
)
''')
        c.execute('''
CREATE UNIQUE INDEX IF NOT EXISTS user_login ON user (login)
''')
        c.execute('''
CREATE TABLE IF NOT EXISTS repo (
    id              integer     primary key,
    user_id         integer,
    repo_url        text,
    name            text,
    description     text,
    language        text,
    FOREIGN KEY (user_id) REFERENCES user (id)
)
''')

    def put_user(self, obj: User):
        c = self.conn.cursor()
        c.execute('INSERT OR REPLACE INTO user VALUES (?, ?, ?)', obj)
        self.conn.commit()

    def get_user(self, *lookup) -> User:
        return self._get(self.list_users, lookup)

    def get_last_user(self) -> User:
        return self._get(self.list_users, {}, order_by='id DESC')

    def list_users(self,
                   *lookup,
                   order_by: str = None,
                   offset: int = None,
                   limit: int = None) -> List[Repo]:
        return self._list(User, 'user', lookup, order_by=order_by,
                          offset=offset, limit=limit)

    def put_repo(self, obj: Repo):
        c = self.conn.cursor()
        c.execute('INSERT OR REPLACE INTO repo VALUES (?, ?, ?, ?, ?, ?)', obj)
        self.conn.commit()

    def get_repo(self, *lookup) -> Repo:
        return self._get(self.list_repos, lookup)

    def list_repos(self,
                   *lookup,
                   order_by: str = None,
                   offset: int = None,
                   limit: int = None) -> List[Repo]:
        return self._list(Repo, 'repo', lookup, order_by=order_by,
                          offset=offset, limit=limit)

    def _get(self, list_method: callable, lookup, *, order_by=None):
        """ Return first result of list_method
        """
        result = list_method(order_by=order_by, limit=1, *lookup)
        return result[0] if result else None

    def _list(self, model, table: str, lookup, *,
              order_by: str = None,
              offset: int = None,
              limit: int = None):
        """ Returns list of `model` objects according filtered by lookup
        """
        if order_by is None:
            order_by = 'id ASC'

        where_clause, values = self._build_where_clause(lookup)
        limit_expr = self._build_limit_expr(offset, limit)
        raw = 'SELECT * FROM {}{} ORDER BY {}{}'.format(table, where_clause,
                                                        order_by, limit_expr)
        c = self.conn.cursor()
        c.execute(raw, values)

        return [model(*row) for row in c.fetchall()]

    def _build_limit_expr(self, offset: int = None, limit: int = None) -> str:
        """ Returns LIMIT expr based on offset and limit
        """
        if limit is None:
            return ''
        else:
            if offset is None:
                offset = 0
            return ' LIMIT {},{}'.format(offset, limit)

    def _build_where_clause(self, lookup: list) -> Tuple[str, list]:
        """ Returns WHERE clause and VALUES for the given lookup
        """
        if not lookup:
            return ('', [])

        where = []
        values = []

        for clause in lookup:
            if isinstance(clause, Q):
                if clause.op in ('<', '>'):
                    where.append('{} {} ?'.format(clause.name, clause.op))
                    values.append(clause.value)
                else:
                    raise NotImplementedError  # pragma: nocover
            elif isinstance(clause, dict):
                for key, value in clause.items():
                    if isinstance(value, str):
                        where.append('{} like ?'.format(key))
                        values.append('%{}%'.format(value.replace('%', '%%')))
                    else:
                        where.append('{} = ?'.format(key))
                        values.append(value)
            else:
                raise NotImplementedError  # pragma: nocover

        where_clause = ' WHERE {}'.format(' AND '.join(where))
        return (where_clause, values)


class LocMemStorage(SQLiteStorage):
    """ In-memory database, used for testing
    """
    def __init__(self):
        super(LocMemStorage, self).__init__(':memory:')
