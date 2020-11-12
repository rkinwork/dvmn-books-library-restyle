import re
from pathlib import Path

import requests

DOWNLOAD_BOOK_URL_TEMPL = 'https://tululu.org/txt.php?id={}'
BOOKS_ROOT = Path('./books')
BOOK_NAME = 'mars_sands.txt'
BOOK_EXISTS_STATUS_CODE = 200
FILENAME_PATTERN = re.compile(r'filename="(.+)"')


def extract_file_name(content_disposition: str) -> [str]:
    if content_disposition is None:
        return
    match = FILENAME_PATTERN.search(content_disposition)
    if match:
        return match.group(1)


def download_book(book_url):
    with requests.get(book_url, stream=True, verify=False) as r:
        if r.status_code != BOOK_EXISTS_STATUS_CODE:
            return
        file_name = extract_file_name(r.headers.get('Content-Disposition'))
        if file_name is None:
            return
        with BOOKS_ROOT.joinpath(file_name).open('wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                f.write(chunk)


def download_books():
    BOOKS_ROOT.mkdir(parents=True, exist_ok=True)
    for book_id in range(1, 11):
        download_book(DOWNLOAD_BOOK_URL_TEMPL.format(book_id))


if __name__ == '__main__':
    download_books()
