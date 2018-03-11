from setuptools import find_packages, setup

import github_scraper

setup(
    name='github_scraper',
    version=github_scraper.__version__,
    description='A simple GitHub scraper using Asyncio.',
    url='https://github.com/caioariede/github-scraper',
    author='Caio Ariede',
    author_email='caio.ariede@gmail.com',
    license='MIT',
    classifiers=[
        'Intended Audience :: Developers',
        'Topic :: Utilities',
        'License :: Public Domain',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.6',
    ],
    packages=find_packages(exclude=['tests']),
    setup_requires=['pytest-runner'],
    tests_require=[
        'pytest==3.4.2',
        'pytest-cov==2.5.1',
        'tox==2.9.1',
    ],
    install_requires=[
        'aiohttp==3.0.7',
        'aioresponses==0.4.0',
        'tenacity==4.9.0',
        'docopt==0.6.2',
        'Flask==0.12.2',
        'Flask-RESTful==0.3.6',
    ],
    entry_points={
        'console_scripts': [
            'github-scraper=github_scraper.cli:main',
        ],
    },
)
