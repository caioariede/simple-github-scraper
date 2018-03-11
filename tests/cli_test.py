from unittest import TestCase, mock

from github_scraper.cli import main

import sys


class CLITest(TestCase):
    def test_scrape(self):
        with mock.patch.object(sys, 'argv', ['', 'scrape']):
            with mock.patch('github_scraper.cli.run_scraper') as run_scraper:
                main()
                assert run_scraper.called

    def test_api(self):
        with mock.patch.object(sys, 'argv', ['', 'api']):
            with mock.patch('github_scraper.cli.get_app') as get_app:
                main()
                assert get_app.called

    def test_main(self):
        with mock.patch('github_scraper.cli.main') as main:
            __import__('github_scraper.__main__')
            assert main.called
