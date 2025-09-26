import glob
import json
import os
import re
from collections import defaultdict
from dateutil.parser import parse as date_parse
from dateutil.parser import ParserError
from typing import Dict, List

import bs4
from bs4 import BeautifulSoup


def parse_thread_filename(thread_filepath: str) -> Dict[str, any]:
    _, thread_filename = os.path.split(thread_filepath)
    pattern = r"crawl_date_(\d{4}-\d{2}-\d{2})-solve_type_(solved|unsolved)-thread_(\d+)-.*page_(\d+)"
    if m := re.search(pattern, thread_filename):
        return {
            'crawl_date': m.group(1),
            'solve_type': m.group(2),
            'thread_id': m.group(3),
            'page_num': m.group(4),
            'page_filepath': thread_filepath
        }
    else:
        raise ValueError(f"invalid thread filename '{thread_filename}'")


def parse_thread_filenames(thread_filenames: List[str]) -> Dict[str, List[Dict[str, any]]]:
    thread_file_map = defaultdict(list)
    for thread_filename in thread_filenames:
        tf_info = parse_thread_filename(thread_filename)
        thread_file_map[tf_info['thread_id']].append(tf_info)
    return thread_file_map


def parse_thread_file(thread_file: str):
    thread_fname = os.path.split(thread_file)[-1]
    crawl_date = thread_fname.split('-solve_type_')[0].replace('crawl_date_', '')
    solve_type = thread_fname.split('-solve_type_')[1].split('-thread')[0]
    if m := re.search(r".*-page_(\d+)", thread_fname):
        page_num = int(m.group(1))
    else:
        print(f"no page number in thread_file '{thread_fname}'")
        page_num = None
    if solve_type not in {'solved', 'unsolved'}:
        print(f"invalid solve_type '{solve_type}' for thread file '{thread_file}'")
    try:
        date_parse(crawl_date)
    except ParserError:
        print(f"invalid crawl date '{crawl_date} for thread file '{thread_file}'")
    with open(thread_file, 'rt') as fh:
        soup = BeautifulSoup(fh, features="lxml")
        topic_details = extract_topic_details(soup)
        comments = extract_comments(soup, thread_file)
        for comment in comments:
            comment['crawl_date'] = crawl_date
            comment['solve_type'] = solve_type
            comment['page_num'] = page_num
    return topic_details, comments


def parse_thread(thread_files_info: List[Dict[str, any]]):
    thread_comments = []
    thread_details = {}
    for tf_info in thread_files_info:
        topic_details, page_comments = parse_thread_file(tf_info['page_filepath'])
        for field in topic_details:
            if field not in thread_details:
                thread_details[field] = topic_details[field]
        thread_comments.extend(page_comments)
    first_comment = thread_comments[0]
    thread_details['crawl_date'] = first_comment['crawl_date']
    thread_details['solve_type'] = first_comment['solve_type']
    thread_details['thread_id'] = first_comment['thread_id']
    for idx, tc in enumerate(thread_comments):
        rank = idx + 1
        tc['message_num'] = rank
    thread_details['num_messages'] = len(thread_comments)
    thread_details['messages'] = thread_comments
    return thread_details


def extract_comment(comment_soup, comment_rank: int, title: str, thread_file: str):
    thread_name = os.path.split(thread_file)[-1].split('-thread_')[-1]
    thread_id = thread_name.split('-')[0]
    if thread_id.isdigit() is False:
        raise ValueError(f"Unexpected thread ID {thread_id} in thread file '{thread_file}'")
    comment_text_elems = []
    comment_date = None
    in_text = False
    for child in comment_soup:
        # print(f"CHILD:", child)
        if child.name == 'strong' and child.find('a') is not None:
            in_text = True
            # print(f"\tUSER")
            continue
        if child.name == 'ul' and 'feedItemCommentFooter' in child.attrs['class']:
            footer = child
            comment_date = footer.find('a').text
            in_text = False
        if in_text is True:
            if isinstance(child, bs4.element.NavigableString):
                # print(f"\tCHILD is NavigableString: #{child.strip()}#")
                comment_text_elems.append(child.strip())
            elif isinstance(child, bs4.element.Tag) and child.name == 'br':
                comment_text_elems.append('\n')
                pass
            else:
                comment_text_elems.append(child.text.strip())
                # print(f"\tSKIPPED CHILD: #{child}#")
    comment_text_elems = [cte for cte in comment_text_elems if cte != '']

    # print("comment_text_elems:", comment_text_elems)
    try:
        strong = comment_soup.find('strong')
        if strong.text.strip() == 'deleted user':
            user_name = 'deleted user'
            user_url = None
        else:
            user_soup = comment_soup.find('strong').find('a')
            user_name = user_soup.text
            user_url = user_soup.attrs['href']
        comment = {
            'thread_name': thread_name,
            'thread_url': f"https://goodreads.com/topic/show/{thread_name}",
            'thread_id': thread_id,
            'thread_title': title,
            'comment_id': comment_soup.attrs['id'],
            'comment_rank': comment_rank,
            'comment_date': comment_date,
            'user_name': user_name,
            'user_url': user_url,
            'comment_text': ' '.join(comment_text_elems)
        }
    except AttributeError:
        print(comment_soup)
        raise
    # print(comment_soup)
    return comment


def extract_thread_title(page_content):
    title_div = page_content.find('h1').find('div')
    title = None
    for child in title_div:
        if "What's the Name of That Book???" in child.text:
            continue
        if re.search(r"\w", child.text):
            title = child.text.strip()
    return title


def extract_topic_details(soup):
    body = soup.find('body')
    page_content = body.find('div', class_='pageContent')
    topic_details = {}
    topic_detail_soup = page_content.find('div', class_='topicDetails')
    topic_author_soup = topic_detail_soup.find('span', class_='topicAuthor')
    stripped_strings = [t for t in topic_author_soup.stripped_strings]
    try:
        if len(stripped_strings) == 3:
            stripped_strings = [t.replace('\n', ' ') for t in stripped_strings]
        elif len(stripped_strings) == 1:
            stripped_strings = stripped_strings[0].split('\n')
        else:
            raise ValueError(f"unexpected number of elements in topic_author_soup: '{topic_author_soup}'")
        _, author_name, creation_date = stripped_strings
    except ValueError:
        print(f"topic_author_soup: {topic_author_soup}")
        print(f"stripped_strings: {stripped_strings}")
        raise
    topic_details['author_name'] = author_name.strip()
    if creation_date.startswith(','):
        creation_date = creation_date[1:]
    topic_details['creation_date'] = creation_date.strip()
    topic_details['view_count'] = None
    topic_details['books_mentions'] = []
    # print(topic_details)
    view_count = topic_detail_soup.find('span', class_="viewCount").text.replace('\n', ' ')
    # print(view_count)
    if m := re.match(r"(\d+) views", view_count.strip()):
        topic_details['view_count'] = int(m.group(1))
    else:
        raise ValueError(f"unexpected format for viewCount: #{view_count}#")
    book_mention_soup = topic_detail_soup.find('div', class_="bookMentions")
    if book_mention_soup is not None:
        for a in book_mention_soup.find_all('a'):
            mention = {
                'book_id': a.attrs['href'].split('/')[-1],
                'book_url': f"https://goodreads.com{a.attrs['href']}",
                'book_name': a.text.strip()
            }
            topic_details['books_mentions'].append(mention)
    return topic_details


def extract_comments(soup, thread_file: str):
    body = soup.find('body')
    page_content = body.find('div', class_='pageContent')
    title = extract_thread_title(page_content)
    comments = page_content.find_all('div', class_='feedItemComment')
    return [extract_comment(comment, ci + 1, title, thread_file) for ci, comment in enumerate(comments)]


def read_html(html_file):
    with open(html_file, 'rt') as fh:
        soup = BeautifulSoup(fh, features="lxml")
        return soup


def parse_thread_row(headers, row):
    base_url = "https://goodreads.com"
    cells_text = [td.text.strip() for td in row.find_all('td')]
    cells = {header: cells_text[hi] for hi, header in enumerate(headers) if header != '' and hi > 1}
    try:
        links = [td.find('a') for td in row.find_all('td') if td.find('a') is not None]
        thread_link = links[0]
        thread = {
            'thread_url': f"{base_url}{thread_link.attrs['href']}",
            'thread_text': thread_link.text.strip(),
            'page_num': 1
        }
        if len(links) == 2:
            user_link = links[1]
            thread['user_url'] = f"{base_url}{user_link.attrs['href']}"
            thread['user_name'] = user_link.text.strip()
        else:
            thread['user_url'] = None
            thread['user_name'] = cells_text[1]
        for field in cells:
            thread[field] = cells[field]
    except ValueError:
        print(row)
        print(cells)
        raise
    return thread


def extract_solve_type_threads(solve_type_file: str):
    soup = read_html(solve_type_file)
    main_content = soup.find('div', class_='mainContent')
    thread_table = main_content.find('table', class_='tableList')
    rows = thread_table.find_all('tr')
    print(f"\trows: {len(rows)}")
    header_row = rows[0]
    thread_rows = rows[1:]

    headers = [th.text.strip() for th in header_row.find_all('th')]
    threads = [parse_thread_row(headers, row) for row in thread_rows]
    return threads


def extract_unsolved_threads(unsolved_file):
    soup = read_html(unsolved_file)
    main_content = soup.find('div', class_='mainContent')
    thread_table = main_content.find('table', class_='tableList')
    rows = thread_table.find_all('tr')
    print(f"\trows: {len(rows)}")
    header_row = rows[0]
    thread_rows = rows[1:]

    headers = [th.text.strip() for th in header_row.find_all('th')]
    threads = []
    base_url = "https://goodreads.com"

    for row in thread_rows:
        cells_text = [td.text.strip() for td in row.find_all('td')]
        cells = {header: cells_text[hi] for hi, header in enumerate(headers) if header != '' and hi > 1}
        try:
            links = [td.find('a') for td in row.find_all('td') if td.find('a') is not None]
            thread_link = links[0]
            thread = {
                'thread_url': f"{base_url}{thread_link.attrs['href']}",
                'thread_text': thread_link.text.strip(),
            }
            if len(links) == 2:
                user_link = links[1]
                thread['user_url'] = f"{base_url}{user_link.attrs['href']}"
                thread['user_name'] = user_link.text.strip()
            else:
                thread['user_url'] = None
                thread['user_name'] = cells_text[1]
            for field in cells:
                thread[field] = cells[field]
        except ValueError:
            print(row)
            print(cells)
            raise
        threads.append(thread)
    return threads


def main():
    thread_dir = '../../../data/books/goodreads_crawl/thread_pages'
    thread_files = glob.glob(os.path.join(thread_dir, f'crawl_date_*'))
    print(f"Number of thread files: {len(thread_files)}")
    thread_file_map = parse_thread_filenames(thread_files)
    out_dir = '../../../data/books/goodreads_crawl/parsed_threads/'

    for thread_id in thread_file_map:
        topic_details = parse_thread(thread_file_map[thread_id])
        out_fname = f"thread_{thread_id}-crawl_date_{topic_details['crawl_date']}-solve_type_{topic_details['solve_type']}.json"
        out_filepath = os.path.join(out_dir, out_fname)
        with open(out_filepath, 'wt') as fh:
            json.dump(topic_details, fh)

    return None


if __name__ == "__main__":
    main()

