from unittest import TestCase, mock
from flask import Flask

from github_scraper.storage.sqlite import LocMemStorage
from github_scraper.models import User, Repo
from github_scraper.api import get_app

import json


class APITest(TestCase):
    def setUp(self):
        self.storage = LocMemStorage()
        self.storage.put_user(User(1, 'mojombo', 'http://github.com/mojombo'))
        self.storage.put_user(User(2, 'defunkt', 'http://github.com/defunkt'))
        self.storage.put_repo(Repo(1, 1, 'http://github.com/mojombo/x', 'x',
                                   'testing 1', 'ruby'))
        self.storage.put_repo(Repo(2, 2, 'http://github.com/defunkt/y', 'y',
                                   'testing 2', 'python'))

    def test_run_api(self):
        with mock.patch.object(Flask, 'run') as run:
            get_app(self.storage).run()
            assert run.called

    def test_list_users(self):
        app = get_app(self.storage).test_client()
        assert json.loads(app.get('/users').data) == [
            {'id': 1,
             'login': 'mojombo',
             'user_url': 'http://github.com/mojombo'},
            {'id': 2,
             'login': 'defunkt',
             'user_url': 'http://github.com/defunkt'},
        ]

    def test_list_users_since(self):
        app = get_app(self.storage).test_client()
        assert json.loads(app.get('/users', data={'since': 1}).data) == [
            {'id': 2,
             'login': 'defunkt',
             'user_url': 'http://github.com/defunkt'},
        ]

    def test_get_user(self):
        app = get_app(self.storage).test_client()
        assert json.loads(app.get('/users/mojombo').data) == {
            'id': 1,
            'login': 'mojombo',
            'user_url': 'http://github.com/mojombo',
        }

    def test_get_user_not_found(self):
        app = get_app(self.storage).test_client()
        assert app.get('/users/unknown').status_code == 404

    def test_list_repos(self):
        app = get_app(self.storage).test_client()
        assert app.get('/users/unknown/repos').status_code == 404
        assert json.loads(app.get('/users/mojombo/repos').data) == [
            {'id': 1,
             'user_id': 1,
             'repo_url': 'http://github.com/mojombo/x',
             'name': 'x',
             'description': 'testing 1',
             'language': 'ruby'},
        ]

    def test_list_repos_filter(self):
        app = get_app(self.storage).test_client()
        data1 = {'description': 'testing'}
        data2 = {'description': 'unkown repo'}
        data3 = {'language': 'ruby'}
        assert app.get('/users/mojombo/repos', data=data1).data != b'[]\n'
        assert app.get('/users/mojombo/repos', data=data2).data == b'[]\n'
        assert app.get('/users/mojombo/repos', data=data3).data != b'[]\n'
