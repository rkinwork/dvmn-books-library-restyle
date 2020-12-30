import argparse
import json
import pathlib
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag

from tululu_lib import SITE_HOST, MEDIA_EXISTS_STATUS_CODE, get_book_by_url

FANTASTIC_CATEGORY_URL = urljoin(SITE_HOST, '/{category}')
FANTASTIC_CATEGORY_CODE = 'l55/'
MAX_PAGES_TO_PROCESS_IN_CATEGORY = 701
DEFAULT_JSON_FILE_NAME = 'fantastic_lib.json'


def extract_fantastic_book_link(source_url: str, table_book: Tag) -> [str]:
    try:
        a_tag = table_book.select_one('.bookimage a')
    except AttributeError:
        return None

    return urljoin(source_url, a_tag['href'])


def process_category_page(category_code: str, page: str = '1'):
    category_url = FANTASTIC_CATEGORY_URL.format(category=category_code)
    url_to_process = urljoin(category_url, page)
    with requests.get(url_to_process, verify=False) as req:
        if req.status_code != MEDIA_EXISTS_STATUS_CODE:
            return None
        response_text = req.text
    soup = BeautifulSoup(response_text, 'lxml')
    table_books = soup.select('table.d_book')
    for table_book in table_books:
        book_link = extract_fantastic_book_link(url_to_process, table_book)
        if book_link:
            yield extract_fantastic_book_link(url_to_process, table_book)


def extract_href_from_category(
        category_code: str,
        start_page: int = 1,
        end_page: int = MAX_PAGES_TO_PROCESS_IN_CATEGORY,
):
    for page in range(start_page, end_page):
        yield from process_category_page(
            category_code=category_code,
            page=str(page),
        )


def main():
    parser = argparse.ArgumentParser(
        description='Download fantastic books from tululu website',
    )
    parser.add_argument(
        '--start_page',
        type=int,
        default=1,
        help='Page in category to start parse books',
    )
    parser.add_argument(
        '--end_page',
        type=int,
        default=MAX_PAGES_TO_PROCESS_IN_CATEGORY + 1,
        help='Page in category to start parse books',
    )
    parser.add_argument(
        '--skip_imgs',
        action='store_true',
        help='Skip book image download',
    )
    parser.add_argument(
        '--skip_txt',
        action='store_true',
        help='Skip boot text download',
    )
    parser.add_argument(
        '--dest_folder',
        type=lambda path_name: pathlib.Path(path_name),
        default='.',
        help='Root folder to save books and imgs',
    )
    parser.add_argument(
        '--json_path',
        type=lambda path_name: pathlib.Path(path_name),
        default=DEFAULT_JSON_FILE_NAME,
        help='Where to save json with lib data',
    )

    args = parser.parse_args()
    data_to_save = []
    books_urls = extract_href_from_category(
        category_code=FANTASTIC_CATEGORY_CODE,
        start_page=args.start_page,
        end_page=args.end_page,
    )
    for book_url in books_urls:
        data_to_save.append(get_book_by_url(
            book_url,
            is_boot_txt_download=not args.skip_txt,
            is_image_download=not args.skip_imgs,
            download_root=args.dest_folder,
        ),
        )
    data_to_save = filter(None, data_to_save)

    book_lib_json_path = args.json_path
    with book_lib_json_path.open(mode='w', encoding='utf-8') as f:
        json.dump(list(data_to_save), f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    main()
