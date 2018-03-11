from unittest import TestCase

from github_scraper.models import User, Repo
from github_scraper.storage.sqlite import LocMemStorage, Q


class SQLiteStorageTest(TestCase):
    def setUp(self):
        self.storage = LocMemStorage()

    def test_put_user_new(self):
        self.storage.put_user(User(1, 'x', 'http://github.com/x'))
        obj = self.storage.get_user({'id': 1})

        assert obj.id == 1
        assert obj.login == 'x'
        assert obj.user_url == 'http://github.com/x'

    def test_put_user_existing(self):
        self.storage.put_user(User(1, 'x', 'http://github.com/x'))
        self.storage.put_user(User(1, 'y', 'http://github.com/x'))
        obj = self.storage.get_user({'id': 1})

        assert obj.id == 1
        assert obj.login == 'y'
        assert obj.user_url == 'http://github.com/x'

    def test_put_repo(self):
        self.storage = LocMemStorage()
        self.storage.put_user(User(id=1,
                                   login='x',
                                   user_url='http://github.com/x'))
        self.storage.put_repo(Repo(id=1,
                                   user_id=1,
                                   repo_url='http://github.com/x/x',
                                   name='x',
                                   description='y',
                                   language='z'))
        obj = self.storage.get_repo({'id': 1})

        assert obj.id == 1
        assert obj.user_id == 1
        assert obj.repo_url == 'http://github.com/x/x'
        assert obj.name == 'x'
        assert obj.description == 'y'
        assert obj.language == 'z'

    def test_context_manager(self):
        with self.storage:
            assert not self.storage.closed
        assert self.storage.closed

    def test_build_where_clause(self):
        empty_test = self.storage._build_where_clause([])
        str_test = self.storage._build_where_clause([{'x': 'y'}])
        int_test = self.storage._build_where_clause([{'x': 162}])
        q_ltgt_test = self.storage._build_where_clause([Q('x') < 1,
                                                        Q('y') > 2])

        assert empty_test == ('', [])
        assert str_test == (' WHERE x like ?', ['%y%'])
        assert int_test == (' WHERE x = ?', [162])
        assert q_ltgt_test == (' WHERE x < ? AND y > ?', [1, 2])

    def test_build_limit_expr(self):
        empty = self.storage._build_limit_expr(offset=None, limit=None)
        offset_only = self.storage._build_limit_expr(offset=10, limit=None)
        limit_only = self.storage._build_limit_expr(offset=None, limit=10)
        limit_offset = self.storage._build_limit_expr(offset=10, limit=12)

        assert empty == ''
        assert offset_only == ''
        assert limit_only == ' LIMIT 0,10'
        assert limit_offset == ' LIMIT 10,12'
