## Тестовое задание Python
Необходимо разработать скрипт на языке Python 3, который будет выполнять следующие функции:

1. Получать данные с документа при помощи Google API, сделанного в [Google Sheets](https://docs.google.com/spreadsheets/d/1f-qZEX1k_3nj5cahOzntYAnvO4ignbyesVO7yuBdv_g/edit) (необходимо копировать в свой Google аккаунт и выдать самому себе права).
2. Данные должны добавляться в БД, в том же виде, что и в файле –источнике, с добавлением колонки «стоимость в руб.»
    * Необходимо создать DB самостоятельно, СУБД на основе PostgreSQL.
    * Данные для перевода $ в рубли необходимо получать по курсу [ЦБ РФ](https://www.cbr.ru/development/SXML/).
3. Скрипт работает постоянно для обеспечения обновления данных в онлайн режиме (необходимо учитывать, что строки в Google Sheets таблицу могут удаляться, добавляться и изменяться).

Дополнения, которые дадут дополнительные баллы и поднимут потенциальный уровень оплаты труда:

1. * Упаковка решения в docker контейнер
   * Разработка функционала проверки соблюдения «срока поставки» из таблицы. В случае, если срок прошел, скрипт отправляет уведомление в Telegram.
   * Разработка одностраничного web-приложения на основе Django или Flask. Front-end React.
******************************
### Задание выполнено с использованием библиотек:
#### Для скрипта
* psycopg2 (для подключения к БД PostgreSQL)
* pygsheets (для подключения к Google sheets API)
* requests
* lxml
* BeautifulSoup4 (для парсинга xml страницы с курсами валют)
#### Для web-приложения
* Django (backend)
* Djnago Rest Framework (для связи backend'a и frontend'a)
* drf-yasg
* django-cors-headers
* React (frontend)
* react-bootstrap (стилистика)
* recharts (график)

### Ссылка на Google table с выданым доступом
[Google table](https://docs.google.com/spreadsheets/d/1N6wLleVKbIJKK1uYm4aV0gT0q03RRwbGwmnUaPHgspY/edit?usp=sharing)


### Зависимости
- Список необходимых библиотек находится в файле requirements.txt и frontend/package.json
- Так-же должены быть установлены Python 3.10, Node.js не ниже версии 14.0.0 и npm не ниже версии 5.6
```sh
pip install -r requirements.txt # в созданном виртуальном окружении
npm install # в дирректории frontend
```

### Настройки
Для корректного подключения к локальной базе данных PostgreSQL, необходимо в файле app/config.py указать свои значения для переменных db_name,db_user,db_password,db_host,db_port. В случае изменения предустановленных параметов базы данных, продублировать эти изменения для DATABASES в kanalservis/kanalservis/settings.py

# Запуск скрипта

```sh
python __init__.py

```
* в директории script

# Запуск Веб-приложения

```sh
python manage.py runserver

```
* в директории backend с активироанным виртуальным окружением (venv)

```sh
npm start

```
* в директории frontend


