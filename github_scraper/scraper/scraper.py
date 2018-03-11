import aiohttp
import asyncio
import sys
import time

from typing import Iterator
from tenacity import retry, retry_if_exception_type, wait_exponential, TryAgain

from ..storage import Storage
from ..models import User, Repo

from .exceptions import ServerError


class Scraper:
    """ Scraper is the class responsible to fetch and put users and
        repositories in the storage. The only method you are supposed to call
        in normal circunstances is :func:`Scraper.run`

        :param storage: :func:`storage.Storage` object to put fetched users
                        and repositories
        :param verbosity: 0 (silent), 1 (minimum), 2 (verbose)
    """
    api_users_endpoint = 'https://api.github.com/users?since={}'
    api_repos_endpoint = 'https://api.github.com/users/{}/repos'

    def __init__(self, storage: Storage, *, verbosity: int):
        self.storage = storage
        self.verbosity = verbosity
        self.stats = {'u': 0, 'r': 0}

    def run(self):
        """ Run the scraper
        """
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.async_fetch_users_and_repos())

        self.print_stats()

    async def async_fetch_users_and_repos(self):
        """ Fetch users and repositories
        """
        async with aiohttp.ClientSession() as session:
            tasks = []
            async for user in self.async_fetch_user_list(session):
                tasks.append(self.async_fetch_repos(session, user.login))
            await asyncio.wait(tasks)

    async def async_fetch_user_list(self,
                                    session: aiohttp.ClientSession,
                                    ) -> Iterator[User]:
        """ Fetch users, put in storage and return
        """
        url = self.api_users_endpoint.format(self.get_last_user_id())
        result = await self.async_get(session, url)
        for user in result:
            obj = User(
                id=user['id'],
                login=user['login'],
                user_url=user['html_url'],
            )
            self.stats['u'] += 1
            self.report_obj(obj)
            self.storage.put_user(obj)
            yield obj

    async def async_fetch_repos(self,
                                session: aiohttp.ClientSession,
                                login: str) -> Iterator[Repo]:
        """ Fetch user's repositories and put in storage
        """
        url = self.api_repos_endpoint.format(login)
        result = await self.async_get(session, url)
        for repo in result:
            obj = Repo(
                id=repo['id'],
                user_id=repo['owner']['id'],
                repo_url=repo['html_url'],
                name=repo['name'],
                description=repo['description'],
                language=repo['language'],
            )
            self.stats['r'] += 1
            self.report_obj(obj)
            self.storage.put_repo(obj)

    @retry(retry=retry_if_exception_type(ServerError),
           wait=wait_exponential(multiplier=1))
    async def async_get(self,
                        session: aiohttp.ClientSession,
                        url: str) -> dict:
        """ GET request and perform response validation. In case of a
            ServerError, for every retry we will increase time exponentially.
        """
        async with session.get(url) as response:
            await self.validate_response(response)
            result = await response.json()
            return result

    async def validate_response(self, response: aiohttp.ClientResponse):
        """ Validate response and look for particular errors
        """
        if response.headers.get('x-ratelimit-remaining') == '0':
            # we're rate-limited, let's wait a bit before proceeding
            reset_time = int(response.headers['x-ratelimit-reset'])
            retry_in = reset_time - time.time()
            if self.verbosity > 0:
                log('\n', 'Rate limit, retrying in {}s\n'.format(retry_in))
            await asyncio.sleep(retry_in)
            raise TryAgain

        if response.status == 500:
            # looks like the server is having problems
            raise ServerError

        response.raise_for_status()

    def get_last_user_id(self) -> int:
        """ Returns last user id we have seen
        """
        last_user = self.storage.get_last_user()
        if last_user:
            return last_user.id
        else:
            return 0

    def report_obj(self, obj):
        """ Report result to command line according to verbosity
        """
        if self.verbosity > 0:
            if self.verbosity > 1:
                log(repr(obj), '\n')
            elif isinstance(obj, User):
                log('u')
            elif isinstance(obj, Repo):
                log('r')

    def print_stats(self):
        """ Print stats for fetched users and repositories
        """
        if self.verbosity > 0:
            log('\n', 'Fetched {u} users and {r} repos'.format(**self.stats))


def log(*messages):
    """ Logs messages to stdout and flush
    """
    for m in messages:
        sys.stdout.write(m)
    sys.stdout.flush()


def run_scraper(*, storage: Storage, verbosity: int):
    """ Run scraper from command line
    """
    try:
        Scraper(storage=storage, verbosity=verbosity).run()
    except KeyboardInterrupt:
        asyncio.gather(*asyncio.Task.all_tasks()).cancel()

        loop = asyncio.get_event_loop()
        loop.stop()
    finally:
        if verbosity > 0:
            log('\n')
        sys.exit(0)
