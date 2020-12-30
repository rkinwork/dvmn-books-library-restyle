import re
from pathlib import Path
from typing import NamedTuple, Tuple
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename

SITE_HOST = 'https://tululu.org/'
DOWNLOAD_BOOK_URL_TEMPL = urljoin(SITE_HOST, 'txt.php?id={}')
BOOKS_ROOT_NAME = 'books'
IMAGES_ROOT_NAME = 'images'
MEDIA_EXISTS_STATUS_CODE = 200
FILENAME_PATTERN = re.compile(r'filename="(.+)"')
BOOK_ID_PATTERN = re.compile(urljoin(SITE_HOST, r'b(\d+)'))
BOOK_NAME_TEMPL = '{book_id}. {book_name}.txt'
AUTHOR_BOOK_NAME_SEPARATOR = ' - '
SKIPPED_DOWNLOAD_PLACEHOLDER = 'download was skipped'


class BookMetadata(NamedTuple):
    author: str = None
    title: str = None
    img_url: str = None
    comments: Tuple[str, ...] = ()
    genres: Tuple[str, ...] = ()


def extract_file_name(content_disposition: str) -> [str]:
    if content_disposition is None:
        return None
    match = FILENAME_PATTERN.search(content_disposition)
    if match:
        return match.group(1)


def get_book_by_url(book_url: str,
                    is_image_download: bool,
                    is_boot_txt_download: bool,
                    download_root: Path,
                    ) -> [dict]:
    book_metadata = get_book_metadata(book_url)
    if book_metadata.title is None:
        return None
    book_id = BOOK_ID_PATTERN.search(book_url).group(1)

    book_path = SKIPPED_DOWNLOAD_PLACEHOLDER
    if is_boot_txt_download:
        book_path = download_txt(
            url=DOWNLOAD_BOOK_URL_TEMPL.format(book_id),
            file_name=BOOK_NAME_TEMPL.format(
                book_id=book_id,
                book_name=book_metadata.title,
            ),
            folder=download_root.as_posix(),
        )
        if book_path is None:
            return None

    image_src = SKIPPED_DOWNLOAD_PLACEHOLDER
    if is_image_download:
        image_src = download_image(url=book_metadata.img_url)

    return {'author': book_metadata.author,
            'title': book_metadata.title,
            'comments': book_metadata.comments,
            'genres': book_metadata.genres,
            'img_src': image_src,
            'book_path': book_path,
            }


def extract_comments(soup: BeautifulSoup) -> Tuple[str, ...]:
    blocks_with_text = soup.select('#content .texts .black')
    return tuple(''.join(block_text.get_text())
                 for block_text in blocks_with_text
                 )


def extract_genres(soup: BeautifulSoup) -> Tuple[str, ...]:
    a_genres = soup.select(
        'span.d_book a',
        href=lambda a_href: a_href.startswith('/l'),
    )
    return tuple(a_genre.string for a_genre in a_genres)


def get_book_metadata(book_url: str) -> BookMetadata:
    """Функция генерации выгрузки ифнформации о книге.

    Args:
        book_url (str): Cсылка на книгу, которую хочется скачать.
    Returns:
        BookMetadata: Кортеж с информацией о книге.

    """
    with requests.get(book_url, verify=False) as req:
        if req.status_code != MEDIA_EXISTS_STATUS_CODE:
            return BookMetadata()
        response_text = req.text
    soup = BeautifulSoup(response_text, 'lxml')
    book_image_tag = soup.select_one('.bookimage a')
    if not book_image_tag or not book_image_tag['title']:
        return BookMetadata()
    author_and_title = book_image_tag['title']
    image_tag = book_image_tag.select_one('img')
    if not image_tag or not image_tag['src']:
        img_url = None
    else:
        img_url = urljoin(book_url, image_tag['src'])

    comments = extract_comments(soup)
    genres = extract_genres(soup)

    author, title = [
        el.strip()
        for el in author_and_title.split(AUTHOR_BOOK_NAME_SEPARATOR, 1)
    ]
    return BookMetadata(
        author=author,
        title=title,
        img_url=img_url,
        comments=comments,
        genres=genres,
    )


def download_txt(url: str, file_name: str, folder: str = '.') -> [str]:
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

        books_folder = Path(folder) / BOOKS_ROOT_NAME
        books_folder.mkdir(parents=True, exist_ok=True)
        txt_file = books_folder.joinpath(sanitize_filename(file_name))
        with txt_file.open('wb') as file_descriptor:
            for chunk in r.iter_content(chunk_size=1024):
                file_descriptor.write(chunk)

        return txt_file.as_posix()


def download_image(url: str, folder: str = '.') -> [str]:
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

        image_folder = Path(folder) / IMAGES_ROOT_NAME
        image_folder.mkdir(parents=True, exist_ok=True)
        image_file = image_folder.joinpath(
            sanitize_filename(url.split('/')[-1]),
        )
        with image_file.open('wb') as file_descriptor:
            for chunk in r.iter_content(chunk_size=1024):
                file_descriptor.write(chunk)

        return image_file.as_posix()
