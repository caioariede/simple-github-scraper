"""
github-scraper

Usage:
    github-scraper scrape [--db=<path>] [--verbosity=<number>]
    github-scraper api [--db=<path>]
    github-scraper -h | --help
    github-scraper --version

Options:
    -h --help                   Show this screen.
    --version                   Show version.
    --db=<path>                 Database path [default: ./data.sqlite]
    -v --verbosity=<number>     Verbosity level [default: 1]
                                -v 0 (silent)
                                -v 1 (minimum)
                                -v 2 (verbose)

"""
from . import __version__
from .storage.sqlite import SQLiteStorage
from .scraper import run_scraper
from .api import get_app

from docopt import docopt


def main():
    options = docopt(__doc__, version=__version__)
    database = options['--db']
    verbosity = int(options['--verbosity'])

    with SQLiteStorage(database) as storage:
        if options.get('scrape'):
            run_scraper(storage=storage, verbosity=verbosity)
        elif options.get('api'):
            get_app(storage).run()
