# why-ki-requests-are-hard


Contains code to crawl known-item requests in forum posts for games, films and books.

## Installation

For running the Python code, just run (assuming you have `pipenv` installed):

```python
pipenv install
```

You can also just use pip to install `bs4` and `playwright`.

## Usage

There are two scripts:

1. `scripts/crawl_goodreads.py` crawls the most recent solved and
    unsolved KI threads on the Goodreads What's the Name of that Book?
    discussion group. There are some parameters that can be modified
    in the `main` function. The threads are stored under
    `data/books/goodreads_crawl/thread_pages`
2. `scripts/parse_goodreads.py` extracts that posts of the crawled threads
    and puts them in a file per thread in
    `data/books/goodreads_crawl/parsed_threads`

## Analysis

For the analysis dependencies, `uv` is required to do `uv run python python-file`.
