
# **Тестовое задание Python**

Необходимо разработать скрипт на языке Python 3, 

который будет выполнять следующие функции:

1. Получать данные с документа при помощи Google API, сделанного в [Google Sheets](https://docs.google.com/spreadsheets/d/1f-qZEX1k_3nj5cahOzntYAnvO4ignbyesVO7yuBdv_g/edit) (необходимо копировать в свой Google аккаунт и выдать самому себе права).
2. Данные должны добавляться в БД, в том же виде, что и в файле –источнике, с добавлением колонки «стоимость в руб.»
    
    a. Необходимо создать DB самостоятельно, СУБД на основе PostgreSQL.
    
    b. Данные для перевода $ в рубли необходимо получать по курсу [ЦБ РФ](https://www.cbr.ru/development/SXML/).
    
3. Скрипт работает постоянно для обеспечения обновления данных в онлайн режиме (необходимо учитывать, что строки в Google Sheets таблицу могут удаляться, добавляться и изменяться).

Дополнения, которые дадут дополнительные баллы и поднимут потенциальный уровень оплаты труда:

1. a. Упаковка решения в docker контейнер
    
    b. Разработка функционала проверки соблюдения «срока поставки» из таблицы. В случае, если срок прошел, скрипт отправляет уведомление в Telegram.
    
    c. Разработка одностраничного web-приложения на основе Django или Flask. Front-end React.
    
    ![Untitled](https://kanalservis.notion.site/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2F6ee6a638-c52e-46a0-9c2d-cb518c955fb1%2FUntitled.png?table=block&id=b1d9d345-46fe-49b7-8909-2884086d4be1&spaceId=dbcc5cf8-15c2-4d75-bb66-44a130d346fa&width=2000&userId=&cache=v2)
    

1. Решение на проверку передается в виде ссылки на проект на Github.
В описании необходимо указать ссылку на ваш Google Sheets документ (открыть права чтения и записи для пользователя [irbispro10@gmail.com](mailto:irbispro10@gmail.com)), а также инструкцию по запуску разработанных скриптов.
******************************

### Ссылка на Google table с выданым доступом
[Google table](https://docs.google.com/spreadsheets/d/1ki8CrRI7vUo0f4JqWiopPh4y7ffxX2BP2uvRg6eqb_0/edit#gid=0)

### Настройки
Для получения уведомлений в Telegramm о вышедших сроках поставки необходимо добавиться в [канал](https://t.me/db_notice).

### Запуск
Скачиваем архив.
Разархивируем.
В полученной папке kanal_test_task-master открываем папку docker.

В папке docker открываем консоль и запускаем командой:
```
 docker-compose run backend python manage.py migrate
```
Создаются контейнеры БД, pgAdmin, script, backent  и frontend, проводится первичное наполнение БД, отправляется сообщение в телеграмм, проходят миграции с django. 

Вводим команду:

```sh
docker-compose up
```
Идем в браузер по адресу http://localhost:3000/
pgAdmin по адресу http://localhost:5050/ 
      PGADMIN_DEFAULT_EMAIL: noemail@gmail.com
      PGADMIN_DEFAULT_PASSWORD: root
