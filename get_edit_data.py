"""Функционал отображения и внесения информации"""

from aiogram import Bot, Dispatcher, types
from config import HOST, USER, PASSWORD, DB_NAME, BOT_TOKEN, DEPARTMENTS
from datetime import date
import psycopg2

# ================= Подключение к боту =================
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
# ======================================================


# Функционал команды /iamanewemployee2023. Команда для регистрации нового сотрудника.
async def iamanewemployee(message: types.Message):
    while True:
        arguments = message.get_args()  # Строка хранящая аргумент команды (отдел работника)
        if not arguments:
            await message.answer("Необходимо вводить название вашего отдела через пробел после команды. Например: "
                                 "<b>/iamanewemployee2023 Инженер</b>", parse_mode='HTML')
            break
        department_exists = False
        # Проверка, был ли введен существующий отдел организации
        for department in DEPARTMENTS:
            if arguments == department:
                department_exists = True
        if not department_exists:
            await message.answer("Указанный отдел не существует. "
                                 f"Попробуйте указать один из следующих : {DEPARTMENTS}")
            break
        try:
            connection = psycopg2.connect(host=HOST, user=USER, password=PASSWORD,
                                          database=DB_NAME)  # Установка соединения
            with connection.cursor() as cursor:
                cursor.execute("INSERT INTO unusedvacs VALUES (%s, %s, 1, 2, 27);", (message.from_user.id, arguments))
                connection.commit()  # Исполнение запроса
            await message.answer("Вы успешно внесены в базу данных сотрудников.")
        except Exception as _ex:
            await message.answer("Вы уже внесены в базу данных сотрудников.")  # Если uuid пользователя уже в БД
        finally:
            if connection:
                connection.close()
            break


async def assign_vacation(user_id, vacation_type, prefer_day, prefer_month):
    try:
        connection = psycopg2.connect(host=HOST, user=USER, password=PASSWORD, database=DB_NAME)  # Установка соединения
        with connection.cursor() as cursor:
            # Первый запрос - вносит пожелание об отпуске
            # Второй запрос - уменьшает количество отгусков выбранного вида на один
            cursor.execute("INSERT INTO wishes (uuid, vacationtype, preferday, prefermonth) VALUES (%s, %s, %s, %s);"
                           "UPDATE unusedvacs SET {} = {} - 1 WHERE uuid = %s;".format(vacation_type, vacation_type),
                           (user_id, vacation_type, prefer_day, prefer_month, user_id))
            connection.commit()  # Исполнение запроса
    except Exception as _ex:
        print('Error - ', _ex)
    finally:
        if connection:
            connection.close()



async def assign_final_smallvacation(user_id, prefer_day, prefer_month):
    try:
        connection = psycopg2.connect(host=HOST, user=USER, password=PASSWORD, database=DB_NAME)  # Установка соединения
        with connection.cursor() as cursor:
            startday = '%s-%s-%s 00:00:00' % (date.today().year + 1, prefer_month, prefer_day)
            endday = '%s-%s-%s 00:00:00' % (date.today().year + 1, prefer_month, int(prefer_day) + 1)
            cursor.execute("INSERT INTO finaldates (uuid, datestart, datetill) VALUES (%s, '%s', '%s');"
                           "UPDATE unusedvacs SET smallvacation = smallvacation - 1 WHERE uuid = %s;" %
                           (user_id, startday, endday, user_id))
            connection.commit()  # Исполнение запроса
    except Exception as _ex:
        print('Error - ', _ex)
    finally:
        if connection:
            connection.close()


async def wipe_system():
    try:
        connection = psycopg2.connect(host=HOST, user=USER, password=PASSWORD, database=DB_NAME)  # Установка соединения
        with connection.cursor() as cursor:
            cursor.execute("TRUNCATE finaldates;"
                           "TRUNCATE wishes;"
                           "UPDATE unusedvacs SET smallvacation = 27;"
                           "UPDATE unusedvacs SET mediumvacation = 2;"
                           "UPDATE unusedvacs SET longvacation = 1;")
            connection.commit()  # Исполнение запроса
    except Exception as _ex:
        print('Error - ', _ex)
    finally:
        if connection:
            connection.close()



