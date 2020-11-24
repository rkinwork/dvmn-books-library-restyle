import re
from pathlib import Path
from typing import NamedTuple
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename

SITE_HOST = 'https://tululu.org/'
DOWNLOAD_BOOK_URL_TEMPL = urljoin(SITE_HOST, 'txt.php?id={}')
PARSE_BOOK_METADATA_URL_TEMPL = urljoin(SITE_HOST, 'b{}/')
BOOKS_ROOT = Path('./books')
MEDIA_EXISTS_STATUS_CODE = 200
FILENAME_PATTERN = re.compile(r'filename="(.+)"')
BOOK_NAME_TEMPL = '{book_id}. {book_name}.txt'
AUTHOR_BOOK_NAME_SEPARATOR = ' - '


class BookMetadata(NamedTuple):
    author: str = None
    title: str = None
    img_url: str = None


def extract_file_name(content_disposition: str) -> [str]:
    if content_disposition is None:
        return
    match = FILENAME_PATTERN.search(content_disposition)
    if match:
        return match.group(1)


def download_book(book_url):
    with requests.get(book_url, stream=True, verify=False) as r:
        if r.status_code != MEDIA_EXISTS_STATUS_CODE:
            return
        file_name = extract_file_name(r.headers.get('Content-Disposition'))
        if file_name is None:
            return
        with BOOKS_ROOT.joinpath(file_name).open('wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                f.write(chunk)


def download_books():
    for book_id in range(1, 11):
        book_metadata = get_book_metadata(book_id)
        if book_metadata.title is None:
            continue
        download_image(book_metadata.img_url)
        download_txt(DOWNLOAD_BOOK_URL_TEMPL.format(book_id),
                     BOOK_NAME_TEMPL.format(book_id=book_id, book_name=book_metadata.title),
                     BOOKS_ROOT)


def get_book_metadata(book_id: int) -> BookMetadata:
    with requests.get(PARSE_BOOK_METADATA_URL_TEMPL.format(book_id), verify=False) as r:
        if r.status_code != MEDIA_EXISTS_STATUS_CODE:
            return BookMetadata()
        response_text = r.text
    soup = BeautifulSoup(response_text, 'lxml')
    res = soup.select('div.bookimage a')
    if not res or not res[0]['title']:
        return BookMetadata()
    book_image_tag = res[0]
    author_and_title = book_image_tag['title']
    image_tag = book_image_tag.find('img')
    if not image_tag or not image_tag['src']:
        img_url = None
    else:
        img_url = urljoin(SITE_HOST, image_tag['src'])

    author, title = [el.strip() for el in author_and_title.split(AUTHOR_BOOK_NAME_SEPARATOR)]
    return BookMetadata(author=author, title=title, img_url=img_url)


def download_txt(url, file_name, folder='books/') -> [str]:
    """Функция для скачивания текстовых файлов.
    Args:
        url (str): Cсылка на текст, который хочется скачать.
        file_name (str): Имя файла, с которым сохранять.
        folder (str): Папка, куда сохранять.
    Returns:
        [str]: Путь до файла, куда сохранён текст.
    """
    with requests.get(url, stream=True, verify=False) as r:
        if r.status_code != MEDIA_EXISTS_STATUS_CODE:
            return None

        if r.history:
            return None

        books_folder = Path(folder)
        books_folder.mkdir(parents=True, exist_ok=True)
        txt_file = books_folder.joinpath(sanitize_filename(file_name))
        with txt_file.open('wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                f.write(chunk)

        return txt_file.as_posix()


def download_image(url, folder='images/') -> [str]:
    """Функция для скачивания картинок.
        Args:
            url (str): Cсылка на картинку, которую хочется скачать.
            folder (str): Папка, куда сохранять.
        Returns:
            [str]: Путь до файла, куда сохранена картинка.
    """
    with requests.get(url, stream=True, verify=False) as r:
        if r.status_code != MEDIA_EXISTS_STATUS_CODE:
            return None

        if r.history:
            return None

        image_folder = Path(folder)
        image_folder.mkdir(parents=True, exist_ok=True)
        image_file = image_folder.joinpath(sanitize_filename(url.split('/')[-1]))
        with image_file.open('wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                f.write(chunk)

        return image_file.as_posix()


if __name__ == '__main__':
    download_books()
