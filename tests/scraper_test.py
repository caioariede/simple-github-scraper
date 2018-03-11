from unittest import TestCase, mock
from aioresponses import aioresponses
from tenacity import wait_none

from github_scraper.scraper import Scraper, run_scraper
from github_scraper.storage.sqlite import LocMemStorage
from github_scraper.models import User, Repo

import asyncio
import aiohttp
import time


RESPONSES = {
    'user_valid': {
        'status': 200,
        'payload': [
            {
                'id': 1,
                'login': 'mojombo',
                'html_url': 'http://github.com/mojombo',
                'repos_url': 'http://api.github.com/users/mojombo/repos',
            },
            {
                'id': 2,
                'login': 'defunkt',
                'html_url': 'http://github.com/defunkt',
                'repos_url': 'http://api.github.com/users/defunkt/repos',
            },
        ],
    },
    'repo_valid_1': {
        'status': 200,
        'payload': [
            {
                'id': 1,
                'user': 'mojombo',
                'html_url': 'http://github.com/mojombo/test',
                'name': 'test',
                'description': 'Just testing',
                'language': 'ruby',
                'owner': {
                    'id': 1,
                },
            },
        ],
    },
    'repo_valid_2': {
        'status': 200,
        'payload': [
            {
                'id': 2,
                'user': 'defunk',
                'html_url': 'http://github.com/defunk/test',
                'name': 'test',
                'description': 'Just testing',
                'language': 'python',
                'owner': {
                    'id': 2,
                },
            },
        ],
    },
    'invalid_timeout': {
        'status': 403,
        'headers': {
            'x-ratelimit-remaining': '0',
            'x-ratelimit-reset': str(int(time.time()) + 1),
        },
    },
    'invalid_error': {
        'status': 500,
    },
}


class ScraperTest(TestCase):
    def setUp(self):
        self.loop = asyncio.get_event_loop()
        self.storage = LocMemStorage()
        self.scraper = Scraper(storage=self.storage, verbosity=1)

        # increase speed of tests disabling wait
        self.scraper.async_get.retry.wait = wait_none()

    def tearDown(self):
        self.storage.close()

    def run_in_loop(self, method, *args, iterate=True):
        """ Test helper that allows running async method inside asyncio loop

            :param iterate: if true returns a list
        """
        async def async_call(method, *args):
            async with aiohttp.ClientSession() as client:
                if iterate:
                    result = []
                    async for obj in method(client, *args):
                        result.append(obj)
                    return result
                else:
                    return await method(client, *args)

        return self.loop.run_until_complete(async_call(method, *args))

    def test_async_get(self):
        """ Test fetch users
        """
        with aioresponses() as mocked:
            url = self.scraper.api_users_endpoint.format(0)
            mocked.get(url, **RESPONSES['user_valid'])
            result = self.run_in_loop(self.scraper.async_get,
                                      url,
                                      iterate=False)
            assert result

    def test_async_get_retry(self):
        """ Test fetch users
        """
        print('RETRY')
        with aioresponses() as mocked:
            url = self.scraper.api_users_endpoint.format(0)
            mocked.get(url, **RESPONSES['invalid_timeout'])
            mocked.get(url, **RESPONSES['user_valid'])
            result = self.run_in_loop(self.scraper.async_get,
                                      url,
                                      iterate=False)
            assert result
        print('DONE')

    def test_async_get_server_error(self):
        """ Test fetch users
        """
        with aioresponses() as mocked:
            url = self.scraper.api_users_endpoint.format(0)
            mocked.get(url, **RESPONSES['invalid_error'])
            mocked.get(url, **RESPONSES['user_valid'])
            result = self.run_in_loop(self.scraper.async_get,
                                      url,
                                      iterate=False)
            assert result

    def test_fetch_user_list_success(self):
        """ Test fetch users
        """
        with aioresponses() as mocked:
            url = self.scraper.api_users_endpoint.format(0)
            mocked.get(url, **RESPONSES['user_valid'])
            result = self.run_in_loop(self.scraper.async_fetch_user_list)

        assert result == [User(1, 'mojombo', 'http://github.com/mojombo'),
                          User(2, 'defunkt', 'http://github.com/defunkt')]

    def test_fetch_user_list_pagination(self):
        """ Test fetch users - should always fetch users after last id
        """
        self.storage.put_user(User(42, 'mojombo', 'http://github.com/mojombo'))
        last_id = 42
        with mock.patch.object(self.scraper, 'async_get') as async_get:
            result = asyncio.Future()
            result.set_result([])
            async_get.return_value = result
            with aioresponses():
                self.run_in_loop(self.scraper.async_fetch_user_list)
                expected_url = self.scraper.api_users_endpoint.format(last_id)
                async_get.assert_called_with(mock.ANY, expected_url)

    def test_fetch_repos_success(self):
        """ Test fetch repos
        """
        with aioresponses() as mocked:
            url = self.scraper.api_repos_endpoint.format('mojombo')
            mocked.get(url, **RESPONSES['repo_valid_1'])
            self.run_in_loop(self.scraper.async_fetch_repos,
                             'mojombo',
                             iterate=False)

        result = self.storage.list_repos()
        assert result == [
            Repo(id=1,
                 user_id=1,
                 repo_url='http://github.com/mojombo/test',
                 name='test',
                 description='Just testing',
                 language='ruby'),
        ]

    def test_fetch_and_store(self):
        """ Test fetch users and repositories
        """
        with aioresponses() as mocked:
            mocked.get(self.scraper.api_users_endpoint.format(0),
                       **RESPONSES['user_valid'])
            mocked.get(self.scraper.api_repos_endpoint.format('mojombo'),
                       **RESPONSES['invalid_error'])
            mocked.get(self.scraper.api_repos_endpoint.format('mojombo'),
                       **RESPONSES['repo_valid_1'])
            mocked.get(self.scraper.api_repos_endpoint.format('defunkt'),
                       **RESPONSES['invalid_timeout'])
            mocked.get(self.scraper.api_repos_endpoint.format('defunkt'),
                       **RESPONSES['repo_valid_2'])

            self.scraper.run()

        assert len(self.storage.list_users()) == 2
        assert len(self.storage.list_repos()) == 2

    def test_report_obj(self):
        """ Test logging report
        """
        obj1 = Repo(id=1,
                    user_id=1,
                    repo_url='http://github.com/mojombo/test',
                    name='test',
                    description='Just testing',
                    language='ruby')

        obj2 = User(1, 'mojombo', 'http://github.com/mojombo')

        module = 'github_scraper.scraper.scraper'
        with mock.patch('{}.log'.format(module)) as log:
            self.scraper.verbosity = 1
            self.scraper.report_obj(obj1)
            self.scraper.report_obj(obj2)
            self.scraper.verbosity = 2
            self.scraper.report_obj(obj1)
            self.scraper.report_obj(obj2)

            assert log.mock_calls == [
                mock.call('r'),
                mock.call('u'),
                mock.call(repr(obj1), '\n'),
                mock.call(repr(obj2), '\n'),
            ]

    def test_run_scraper(self):
        module = 'github_scraper.scraper.scraper'
        with mock.patch('{}.sys.exit'.format(module)) as exit:
            with mock.patch('{}.Scraper.run'.format(module)) as run:
                run_scraper(storage=LocMemStorage(), verbosity=1)
                assert run.called
                assert mock.call(0) in exit.mock_calls

        # test interrupt
        with mock.patch('{}.sys.exit'.format(module)) as exit:
            def _interrupt():
                raise KeyboardInterrupt
            with mock.patch('{}.Scraper.run'.format(module),
                            side_effect=_interrupt):
                run_scraper(storage=LocMemStorage(), verbosity=1)
                assert mock.call(0) in exit.mock_calls
