# Парсер книг с сайта tululu.org

Скачиваем книги из категории фантастика с сайта [tululu.org](https://tululu.org/l55/)

### Как установить

Для запуска сайта вам понадобится Python третьей версии.

Скачайте код с GitHub. Установите зависимости:

```sh
pip install -r requirements.txt
```

### Для старта

Скачаем книги с первой страницы категории фантастика
```shell script
python3 parse_tululu_category.py --start_page 1 --end_page2
```

Скачаем книги с первой страницы, но без картинок
```shell script
python3 parse_tululu_category.py --start_page 1 --end_page2 --skip_imgs
```

### Аргументы

Полный список, аргументов можно получить

```shell script
python3 parse_tululu_category.py -h
```


| Аргумент      | Описание      | По-умолчанию  |
| ------------- |-------------| -----|
| --start_page  | Страница с которой можно начать скачку книжек | 1 |
| --end_page      | До какой страницы можно скачать книги(не включая) |   702 |
| --skip_imgs | Пропустить скачивание картинок |  `False` |
| --skip_txt | Не скачивать сами книги | `False` |
| --dest_folder  | Папка куда будут скачиваться картинки и книги | `./` |
| --json_path   | Имя и путь файлу куда сохраниться скаченная база | `./fantastic_lib.json` |


### Как сгенерировать сайт

Убедитесь, что после парсинга библиотеки у вас появился файл -  `fantastic_lib.json`

Запустите
```shell script
python3 render_website.py
```

И переходите по адресу http://127.0.0.1:5500

Готовый пример вы можете посмотреть [https://rkinwork.github.io/dvmn-books-library-restyle/](https://rkinwork.github.io/dvmn-books-library-restyle/)


### Цель проекта

Код написан в образовательных целях на онлайн-курсе для веб-разработчиков [dvmn.org](https://dvmn.org/).