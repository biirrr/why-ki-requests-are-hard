import datetime
import glob
import os
import re
import time
from typing import Dict, List, Union

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, Playwright
from playwright._impl._errors import TimeoutError
from playwright._impl._errors import Error

from parse_goodreads import extract_solve_type_threads


def read_list_page_filenames(solve_type: Dict[str, any]):
    fname = f'solve_type_{solve_type["solve_type"]}-tag_{solve_type["tag"]}-page_*-date_{solve_type["crawl_date"]}.html'
    return glob.glob(os.path.join(solve_type['page_dir'], fname))


def get_solve_type_threads(solve_type_files: List[str]):
    all_threads = []
    for solve_type_file in sorted(solve_type_files):
        threads = extract_solve_type_threads(solve_type_file)
        all_threads.extend(threads)
    return all_threads


def fetch_html(playwright: Playwright, url: str,
               wait_time: float = 5.0, max_attempts: int = 5) -> Union[str, None]:
    webkit = playwright.webkit
    iphone = playwright.devices["iPhone 6"]
    browser = webkit.launch()
    context = browser.new_context(**iphone)
    page = context.new_page()
    attempt = 0
    while attempt < max_attempts:
        try:
            page.goto(url)
            html = page.inner_html('html')
            browser.close()
            time.sleep(wait_time)
            return html
        except (TimeoutError, Error):
            attempt += 1
            time.sleep(wait_time)
    if attempt == max_attempts:
        print(f"failed crawling thread {url}")
        browser.close()
    return None


def crawl_solve_type_list_pages(solve_type: Dict[str, any]):
    for page in range(1, solve_type['num_pages'] + 1):
        if page == 1:
            url = solve_type['group_url']
        else:
            url = f"{solve_type['group_url']}&page={page}"
        with sync_playwright() as playwright:
            today = datetime.date.today().isoformat()
            if os.path.exists(solve_type['page_dir']) is False:
                os.mkdir(solve_type['page_dir'])
            fname = f'solve_type_{solve_type["solve_type"]}-tag_{solve_type["tag"]}-page_{page}-date_{today}.html'
            list_page_filepath = os.path.join(solve_type['page_dir'], fname)
            if os.path.exists(list_page_filepath):
                continue
            html = fetch_html(playwright, url)
            with open(list_page_filepath, 'wt') as fh:
                fh.write(html)
            time.sleep(5)


def crawl_thread_page(playwright: Playwright, solve_type: Dict[str, any], thread: Dict[str, any],
                      thread_dir: str, wait_time: float, max_attempts: int = 5):
    base_name = thread['thread_url'].split('/topic/show/')[-1]
    print(f"crawling thread {base_name}, page {thread['page_num']}")
    fname = (f"crawl_date_{solve_type['crawl_date']}-solve_type_{solve_type['solve_type']}"
             f"-thread_{base_name}-page_{thread['page_num']}")
    thread_file = os.path.join(thread_dir, fname)
    thread_page_url = f"{thread['thread_url']}?page={thread['page_num']}"
    if os.path.exists(thread_file):
        return None
    html = fetch_html(playwright, thread_page_url, wait_time=wait_time, max_attempts=max_attempts)
    if html is None:
        return None
    with open(thread_file, 'wt') as fh:
        fh.write(html)
    return html


def get_thread_next_page_num(html):
    page_soup = BeautifulSoup(html, features="lxml")
    page_soup.find('div', class_='normalText')
    next_page_link = page_soup.find('a', class_='next_page')
    if next_page_link is None:
        return None
    if 'href' not in next_page_link.attrs:
        print(f"next page link has no 'href': {next_page_link}")
        return None
    next_page_url = next_page_link.attrs['href']
    if m := re.search(r"\?page=(\d+)", next_page_url):
        return int(m.group(1))
    return None


def crawl_thread(playwright: Playwright, solve_type: Dict[str, any], thread_dir: str,
                 thread: Dict[str, any], wait_time: float = 5.0):
    while True:
        html = crawl_thread_page(playwright, solve_type, thread, thread_dir,
                                 wait_time=wait_time)
        if html is None:
            return None
        next_page_num = get_thread_next_page_num(html)
        if next_page_num is None:
            return None
        elif thread['page_num'] >= next_page_num:
            print(thread)
            print(f'WARNING next_page_num lower or equal to current page_num {next_page_num}')
            return None
        else:
            thread['page_num'] = next_page_num


def crawl_threads(solve_type: Dict[str, any], thread_dir: str,
                  threads: List[Dict[str, any]], wait_time: float = 5.0):
    with sync_playwright() as playwright:
        for thread in threads:
            crawl_thread(playwright, solve_type, thread_dir, thread, wait_time=wait_time)
    return None


def main():
    today = datetime.date.today().isoformat()
    crawl_date = today
    solve_types = [
        {
            'solve_type': 'unsolved',
            'group_url': "https://www.goodreads.com/topic/group_folder/2198?group_id=185",
            'tag': 'unsolved',
            'page_dir': '../../../data/books/goodreads_crawl/unsolved_pages',
            'num_pages': 20,
            'crawl_date': today
        },
        {
            'solve_type': 'solved',
            'group_url': "https://www.goodreads.com/topic/group_folder/990?group_id=185",
            'tag': 'adult_fiction',
            'page_dir': '../../../data/books/goodreads_crawl/solved_pages',
            'num_pages': 20,
            'crawl_date': today
        },
        {
            'solve_type': 'solved',
            'group_url': "https://www.goodreads.com/topic/group_folder/988?group_id=185",
            'tag': 'children_ya',
            'page_dir': '../../../data/books/goodreads_crawl/solved_pages',
            'num_pages': 20,
            'crawl_date': today
        },
        {
            'solve_type': 'solved',
            'group_url': "https://www.goodreads.com/topic/group_folder/991?group_id=185",
            'tag': 'non_fiction',
            'page_dir': '../../../data/books/goodreads_crawl/solved_pages',
            'num_pages': 20,
            'crawl_date': today
        },
        {
            'solve_type': 'solved',
            'group_url': "https://www.goodreads.com/topic/group_folder/1001?group_id=185",
            'tag': 'other_fiction',
            'page_dir': '../../../data/books/goodreads_crawl/solved_pages',
            'num_pages': 20,
            'crawl_date': today
        }
    ]

    thread_dir = '../../../data/books/goodreads_crawl/thread_pages'
    if os.path.exists(thread_dir) is False:
        os.mkdir(thread_dir)

    for solve_type in solve_types[1:]:
        print(f"crawling {solve_type['solve_type']} thread pages in crawl date {crawl_date}")
        crawl_solve_type_list_pages(solve_type)
        solve_type_files = read_list_page_filenames(solve_type)
        print(f'number of {solve_type["solve_type"]} files: {len(solve_type_files)}')
        all_threads = get_solve_type_threads(solve_type_files)
        print(f"number of {solve_type['solve_type']} threads: {len(all_threads)}")
        crawl_threads(solve_type, thread_dir, all_threads)


if __name__ == "__main__":
    main()
