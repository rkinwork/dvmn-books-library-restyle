import argparse
from urllib.parse import urljoin
import json
from pathlib import Path

import requests
from bs4 import BeautifulSoup, Tag

from main import SITE_HOST, MEDIA_EXISTS_STATUS_CODE, get_book_by_url

FANTASTIC_CATEGORY_URL = urljoin(SITE_HOST, '/{category}')
FANTASTIC_CATEGORY_CODE = 'l55/'
MAX_PAGES_TO_PROCESS_IN_CATEGORY = 701
FANTASTIC_LIB_JSON = Path('fantastic_lib.json')


def extract_fantastic_book_link(table_book: Tag) -> [str]:
    try:
        a_tag = table_book.select_one('.bookimage a')
    except AttributeError:
        return None

    return urljoin(SITE_HOST, a_tag['href'])


def process_category_page(category_code: str, page: str = "1"):
    category_url = FANTASTIC_CATEGORY_URL.format(category=category_code)
    url_to_process = urljoin(category_url, page)
    with requests.get(url_to_process, verify=False) as r:
        if r.status_code != MEDIA_EXISTS_STATUS_CODE:
            return None
        response_text = r.text
    soup = BeautifulSoup(response_text, 'lxml')
    table_books = soup.select('table.d_book')
    # for table_book in table_books[:4]:
    #     yield extract_fantastic_book_link(table_book)

    return filter(None, (extract_fantastic_book_link(table_book) for table_book in table_books))


def extract_href_from_category(category_code: str,
                               start_page: int = 1,
                               end_page: int = MAX_PAGES_TO_PROCESS_IN_CATEGORY + 1):
    for page in range(start_page, end_page):
        yield from process_category_page(category_code=category_code, page=str(page))


def main():
    parser = argparse.ArgumentParser(
        description='Download fantastic books from tululu website'
    )
    parser.add_argument('--start_page', type=int, default=1, help='Page in category to start parse books')
    parser.add_argument('--end_page', type=int, default=MAX_PAGES_TO_PROCESS_IN_CATEGORY+1,
                        help='Page in category to start parse books')
    args = parser.parse_args()
    data_to_save = filter(None, (get_book_by_url(book_url) for book_url in
                                 extract_href_from_category(FANTASTIC_CATEGORY_CODE,
                                                            start_page=args.start_page,
                                                            end_page=args.end_page)))
    with FANTASTIC_LIB_JSON.open(mode='w', encoding='utf-8') as f:
        json.dump(list(data_to_save), f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    main()
