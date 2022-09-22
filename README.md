
# Приложение для интеграции с Google API
Cкрипт на  Python, который будет выполнять следующие функции:

1) Получать данные с документа при помощи Google API, сделанного в [Google Sheets](https://docs.google.com/spreadsheets/d/1f-qZEX1k_3nj5cahOzntYAnvO4ignbyesVO7yuBdv_g/edit).
2) Данные должны добавляться в БД, в том же виде, что и в файле–источнике, с добавлением колонки «стоимость в руб.» 
3) Данные для перевода $ в рубли получаются по курсу [ЦБ РФ](https://www.cbr.ru/development/SXML/).
    
4) Скрипт работает постоянно для обеспечения обновления данных в онлайн режиме (необходимо учитывать, что строки в Google Sheets таблицу могут удаляться, добавляться и изменяться).

5) Функционал проверки соблюдения «срока поставки» из таблицы. В случае, если срок прошел, скрипт отправляет уведомление в Telegram.

6) Упаковка решения в docker контейнер
    
7) Одностраничное web-приложение на основе Django или Flask. Front-end React. 
   
___
### Ссылка на Google table с выданым доступом
[Google table](https://docs.google.com/spreadsheets/d/1ki8CrRI7vUo0f4JqWiopPh4y7ffxX2BP2uvRg6eqb_0/edit#gid=0)
___
### Настройки
Для получения уведомлений в Telegramm о вышедших сроках поставки необходимо добавиться в [канал](https://t.me/db_notice).
___
### Запуск
Скачиваем архив.
Разархивируем.
В полученной папке kanal_test_task-master открываем папку docker.

В папке docker открываем консоль и запускаем командой:

```sh
docker-compose up -в
```
___

Одностраничное web-приложение по адресу http://localhost:3000/

pgAdmin по адресу http://localhost:5050/ 

PGADMIN_DEFAULT_EMAIL:             

    noemail@gmail.com
PGADMIN_DEFAULT_PASSWORD:
            
    root
