from typing import TextIO, Tuple
import json
from pathlib import Path
import math
from distutils.dir_util import copy_tree, remove_tree

from jinja2 import Environment, FileSystemLoader, select_autoescape
from livereload import Server
import more_itertools

PAGES = Path('docs')
PAGES_TEMPLATE = "index{}.html"
PAGE_CHUNK = 6
STATIC_PATH = Path('static')
MEDIA_BOOKS_PATH = Path('books')
MEDIA_IMAGES_PATH = Path('images')
FIRST_PAGE_NUMBER = 1


class BookItemException(Exception):
    pass


class BookItem:
    def __init__(self,
                 author: str,
                 title: str,
                 comments: [Tuple] = None,
                 genres: [Tuple] = None,
                 img_src: [str] = None,
                 book_path: [str] = None
                 ):
        self.author = author
        self.title = title
        self.comments = comments
        self.genres = genres
        self.img_src = img_src
        self.book_path = book_path

    @classmethod
    def from_dict(cls, raw_dict: dict):
        return cls(
            author=raw_dict['author'],
            title=raw_dict['title'],
            comments=raw_dict.get('comments'),
            genres=raw_dict.get('genres'),
            img_src=raw_dict.get('img_src'),
            book_path=raw_dict.get('book_path')
        )

    @property
    def alt(self):
        return f"{self.title} - {self.author}"

    @property
    def book_url(self):
        return f"/{self.book_path}"


class BookItems:
    def __init__(self, json_fp: TextIO):
        self._raw_book_items: list = json.load(json_fp)
        self._validate(self._raw_book_items)

    @staticmethod
    def _validate(raw_book_items):
        if len(raw_book_items) == 0:
            raise BookItemException("Raw file should be list and consists of at least with one element")

    def __call__(self, *args, **kwargs):
        for raw_book_item in self._raw_book_items:
            yield BookItem.from_dict(raw_book_item)


def init_template():
    env = Environment(
        loader=FileSystemLoader("templates"),
        autoescape=select_autoescape(['html'])
    )
    return env.get_template("template.html")


def get_book_items() -> list:
    with open('fantastic_lib.json') as f:
        return list(BookItems(f)())


def on_reload():
    if PAGES.exists():
        remove_tree(PAGES)
    copy_tree(STATIC_PATH.as_posix(), (PAGES/'static').as_posix())
    copy_tree(MEDIA_BOOKS_PATH.as_posix(), (PAGES/'books').as_posix())
    copy_tree(MEDIA_IMAGES_PATH.as_posix(), (PAGES/'images').as_posix())

    template = init_template()
    book_items = get_book_items()
    total_pages = math.ceil(len(book_items) / PAGE_CHUNK)

    chunked_books = []
    pages_names = []
    for page_num, book_chunk in enumerate(more_itertools.chunked(book_items, PAGE_CHUNK), 1):
        chunked_books.append(book_chunk)
        page_num = page_num if page_num != FIRST_PAGE_NUMBER else ''
        pages_names.append(PAGES_TEMPLATE.format(page_num))

    for num, book_chunk in enumerate(chunked_books, 1):
        rendered_page = template.render(book_items=book_chunk,
                                        pages_names=pages_names,
                                        paginator_total_pages=total_pages,
                                        current_page=num,
                                        )

        Path(PAGES, pages_names[num - 1]).write_text(rendered_page)


def main():
    server = Server()
    on_reload()
    server.watch('templates/*.html', on_reload)
    server.serve(root=PAGES)


if __name__ == '__main__':
    main()
