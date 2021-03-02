from typing import TextIO, Tuple
import json

from jinja2 import Environment, FileSystemLoader, select_autoescape
from livereload import Server


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
    template = init_template()
    book_items = get_book_items()
    rendered_page = template.render(book_items=book_items)
    with open('index.html', 'w') as f:
        f.write(rendered_page)


def main():
    server = Server()
    on_reload()
    server.watch('templates/*.html', on_reload)
    server.serve()


if __name__ == '__main__':
    main()
