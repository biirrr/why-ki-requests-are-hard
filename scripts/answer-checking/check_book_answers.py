import glob
import gzip
import json
import re
import requests
import time
import urllib
from typing import Dict, List
from unidecode import unidecode

import numpy as np
import pandas as pd
from fuzzy_search.tokenization.token import Tokenizer

from chiir_2026_settings import spreadsheet_urls


BASE_URL = "https://openlibrary.org/search.json"


def normalise_string(text_string: str, tokenizer: Tokenizer):
    if text_string is None or pd.isna(text_string):
        return ''
    text_string = unidecode(text_string)
    tokens = tokenizer.tokenize(text_string)
    return ' '.join([token.n for token in tokens])


def is_flex_match_doc(answer_title, answer_author, doc, tokenizer: Tokenizer):
    doc_title = normalise_string(doc['title'], tokenizer)
    try:
        doc_authors = get_oa_authors(doc, tokenizer)
    except AttributeError:
        print(doc['author_name'])
        raise
    if answer_author is not None and len(doc_authors) > 0:
        return any(is_flex_match(answer_author, doc_author) for doc_author in doc_authors)
    return is_flex_match(answer_title, doc_title)


def get_oa_authors(doc, tokenizer: Tokenizer, normalise: bool = True):
    if 'author_name' not in doc:
        return []
    if normalise is True:
        return [normalise_string(author, tokenizer) for author in doc['author_name']]
    else:
        return [author for author in doc['author_name']]


def is_flex_match(answer_string, oa_string):
    return answer_string == oa_string or answer_string in oa_string or oa_string in answer_string


def get_flex_match_doc(record, response_field, tokenizer: Tokenizer):
    """Check all Open Library search response documents against the answer and
    return the first that matches author and title."""
    answer_title = normalise_string(record['answer'], tokenizer)
    answer_author = normalise_string(record['author'], tokenizer)
    for doc in record[response_field]['docs']:
        if is_flex_match_doc(answer_title, answer_author, doc, tokenizer):
            return doc
    return None


def get_records_files():
    base_filename = '../../../data/books/records-open_library-request_answers'
    return glob.glob(f'{base_filename}_v*.json.gz')


def get_records_file_version(records_file):
    if m := re.search(r"_v(\d+)\.json.gz$", records_file):
        return int(m.group(1))
    else:
        raise ValueError(f"invalid records_file name {records_file}.")


def get_records_file_versions():
    records_files = get_records_files()
    return [(get_records_file_version(rf), rf) for rf in records_files]


def determine_new_version_number():
    return determine_last_version_number() + 1


def determine_last_version_number():
    file_versions = get_records_file_versions()
    if len(file_versions) == 0:
        return 0
    latest = max(version for version, _ in file_versions)
    return latest


def write_book_answer_records(records: List[Dict[str, any]]):
    version_num = determine_new_version_number()
    records_file = f'../data/books/records-open_library-request_answers_v{version_num}.json.gz'
    if len(records) == 1481 and all('response' in record for record in records):
        with gzip.open(records_file, 'wt') as fh:
            json.dump(records, fh)


def read_book_answer_records():
    version_num = determine_last_version_number()
    records_file = f'../../../data/books/records-open_library-request_answers-v{version_num}.json.gz'
    with open(records_file, 'rt') as fh:
        return json.load(fh)


def extract_readinglog(records: List[Dict[str, any]]):
    response_field = 'response_qta'
    no_match = 0
    tokenizer = Tokenizer(ignorecase=True, remove_punctuation=True)

    readinglog_rows = []
    for ri, record in enumerate(records):
        if record[response_field]['num_found'] == 0:
            response_field = 'response_q'
        if record[response_field]['num_found'] == 0:
            continue
        doc = get_flex_match_doc(record, response_field, tokenizer)
        if doc is not None:
            readinglog_count = doc['readinglog_count'] if 'readinglog_count' in doc else 0
            answer_id = f"https://openlibrary.org{doc['key']}"
            doc_title = doc['title']
            doc_author = '; '.join(get_oa_authors(doc, normalise=False))
        else:
            readinglog_count = 0
            answer_id = None
            doc_title = None
            doc_author = None
            no_match += 1
            print(f"no match {no_match}: record num {ri}\treadinglog_count: {readinglog_count}")
        row = [ri, record['thread_id'], record['answer'], record['author'], answer_id, doc_title, doc_author,
               readinglog_count]
        if len(row) > 8:
            print(row)
            break
        readinglog_rows.append(row)
    readinglog_cols = [
        'req_no', 'thread_id', 'answer_title', 'answer_author',
        'work_id', 'work_title','work_author', 'readinglog_count'
    ]
    readinglog_df = pd.DataFrame(readinglog_rows, columns=readinglog_cols)
    return readinglog_df


def search_openlibrary(title: str, max_retries: int = 5):
    """Search the Open Library API for a book title"""
    # url-encoded title and author
    title = re.sub(f' +', '+', title)
    title = urllib.parse.quote_plus(title)
    url = f'{BASE_URL}?q={title}&fields=*'
    response = requests.get(url)
    retry = 0
    while retry < max_retries:
        if response.status_code == 200:
            return response.json()
        else:
            print(response.status_code, f"retry {retry} of {max_retries}, error for title #{title}#")
            retry += 1
            time.sleep(2)


def fetch_openlibrary_matches(records: List[Dict[str, any]]):
    """Check the thread answers against the Open Library book search API and
    add the API response to the records."""
    for ri, record in enumerate(records):
        title = record['answer']
        record['response_qt'] = search_openlibrary(title)
        if pd.isna(record['author']):
            record['response_qta'] = record['response_qt']
        else:
            title_author = f'{title} {record["author"]}'
            record['response_qta'] = search_openlibrary(title_author)
            # crawl delay is 10 seconds according to https://openlibrary.org/robots.txt
            time.sleep(10)
        if (ri + 1) % 10 == 0:
            print(f"{ri + 1} of {len(records)} records processed")


def download_solved_data(spreadsheet_url):
    response = requests.get(spreadsheet_url)
    if response.status_code != 200:
        raise ValueError(f"Error downloading solved data from spreadsheet URL {spreadsheet_url}")
    lines = response.text.split('\r\n')
    rows = [line.split('\t') for line in lines]
    headers = rows.pop(0)
    return pd.DataFrame(rows, columns=headers)


def extract_author(note: str):
    """Extract the author name from the note field."""
    if note.startswith('by ') is False:
        return np.nan
    if ' part of ' in note:
        part_idx = note.index(' part of ')
        # print(note[part_idx:])
        return note[3:part_idx]
    else:
        return note[3:]


def sanity_checks_books(solved_df: pd.DataFrame):
    non_gr_threads = [sr for sr in solved_df.subreddit.unique() if sr != 'goodreads' is False]
    if len(non_gr_threads) > 0:
        raise ValueError(f"subreddit should only contain 'goodreads' but encountered {non_gr_threads}")


def main_books():
    books_url = spreadsheet_urls['books_solved']
    solved_df = download_solved_data(books_url)
    sanity_checks_books(solved_df)
    solved_df['has_author'] = solved_df.notes.apply(lambda x: x.startswith('by '))
    solved_df['author'] = solved_df.notes.apply(extract_author)
    answer_df = solved_df[solved_df.answer.apply(lambda x: pd.notna(x) and x != '')]
    records = answer_df[['thread_id', 'answer', 'author']].to_dict('records')
    readinglog_df = extract_readinglog(records)
    readinglog_df.to_csv("../../../data/books/book_answers-popularity.tsv", sep='\t', index=False)


if __name__ == "__main__":
    main_books()
