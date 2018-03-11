# simple-github-scraper

[![Build Status](https://travis-ci.org/caioariede/simple-github-scraper.svg?branch=master)](https://travis-ci.org/caioariede/simple-github-scraper) [![codecov](https://codecov.io/gh/caioariede/simple-github-scraper/branch/master/graph/badge.svg)](https://codecov.io/gh/caioariede/simple-github-scraper/branch/master)

This is a simple Github Scraper that scrapes user and repository data using Python's asyncio and put the fetched data in a persistent storage (SQLite). It also disposes of a simple API to browse the persisted objects.

* [Install and use](#install-and-use)
* [Running from source code](#running-from-source-code)
* [Testing](#testing)
* [General overview and design decisions](#general-overview-and-design-decisions)

## Install and use

This project requires **Python 3.6** at least, and can be installed as:

```
pip install https://github.com/caioariede/simple-github-scraper/archive/caioariede/dev.zip
```

### Usage

```
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
```

## Running from source code

You can also run it directly from the source code.

**To run the scraper:**

```
python -m github_scraper scrape
```

**To run the API:**

```
python -m github_scraper api
```

**To see available options:**

```
python -m github_scraper -h
```

## Testing

pytest is used for testing. You can run it with a single command:

```
python setup.py
```

If you wanna see test coverage, run:

```
pytest tests --cov=github_scraper --cov-report=term-missing
```

## General overview and design decisions

The project is divided in three main components:

* **Scraper** uses asyncio to fetch user and repository data
* **Storage** disposes an interface to store and retrieve persistent data
* **API** allows browsing persisted data

### Scraper

The design decision behind using asyncio for scraping data is that making multiple HTTP requests can be painfully slow, as you need to wait for each response. To overcome this issue, asyncio is used to perform HTTP requests in parallel.

### Storage

SQLite was chosen to persist data. It's a great relational database with built-in support in Python. The Storage was developed in a way that it easily allows other storages to be implemented, by just extending the Storage class.

### API

Flask RESTful is used to expose a simple API that allows browsing the persisted data.

These are the current endpoints:

* `/users` -- list users
* `/users?since=<num>` -- list users where `id > [num]`
* `/users/<user>` -- user details
* `/users/<user>/repos` -- user repositories

### Python 3

This project used Python 3 and typing, as a way of self-documenting and to improve code quality. Typing can help catching errors during development stage and it gives a quick visual feedback when you are just reading code.
