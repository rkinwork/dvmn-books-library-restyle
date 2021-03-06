import argparse
import json
import pathlib
from urllib.parse import urljoin
import logging

import requests
from bs4 import BeautifulSoup, Tag

from tululu_lib import SITE_HOST, MEDIA_EXISTS_STATUS_CODE, get_book_by_url, TululuException

FANTASTIC_CATEGORY_URL = urljoin(SITE_HOST, '/{category}')
FANTASTIC_CATEGORY_CODE = 'l55/'
MAX_PAGES_TO_PROCESS_IN_CATEGORY = 702
DEFAULT_JSON_FILE_NAME = 'fantastic_lib.json'


def extract_fantastic_book_link(source_url: str, table_book: Tag) -> [str]:
    try:
        a_tag = table_book.select_one('.bookimage a')
    except AttributeError:
        return None

    return urljoin(source_url, a_tag['href'])


def extract_href_from_category(
        category_code: str,
        start_page: int = 1,
        end_page: int = MAX_PAGES_TO_PROCESS_IN_CATEGORY,
):
    for page in range(start_page, end_page):
        category_url = FANTASTIC_CATEGORY_URL.format(category=category_code)
        url_to_process = urljoin(category_url, str(page))
        with requests.get(url_to_process, verify=False) as req:
            if req.status_code != MEDIA_EXISTS_STATUS_CODE:
                logging.error(f"There are problems with url {url_to_process}")
                continue
            response_text = req.text
        table_books = BeautifulSoup(response_text, 'lxml').select('table.d_book')
        yield from (extract_fantastic_book_link(url_to_process, table_book) for table_book in table_books)


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
        default=MAX_PAGES_TO_PROCESS_IN_CATEGORY,
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

    books_urls = extract_href_from_category(
        category_code=FANTASTIC_CATEGORY_CODE,
        start_page=args.start_page,
        end_page=args.end_page,
    )
    if books_urls is None:
        logging.error(f"There are no books in category {FANTASTIC_CATEGORY_CODE}. It's abnormal")
        return

    books_properties_to_save = []
    for book_url in books_urls:
        try:
            book_properties = get_book_by_url(
                book_url,
                is_boot_txt_download=not args.skip_txt,
                is_image_download=not args.skip_imgs,
                download_root=args.dest_folder,
            )
        except TululuException as e:
            logging.error(e)
            continue
        books_properties_to_save.append(book_properties)

    book_lib_json_path = args.json_path
    with book_lib_json_path.open(mode='w', encoding='utf-8') as f:
        json.dump(books_properties_to_save, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    main()
