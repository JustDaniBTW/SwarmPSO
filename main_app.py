"""Телеграм бот."""

from aiogram import Bot, Dispatcher, executor, types
from get_edit_data import iamanewemployee, assign_vacation, assign_final_smallvacation, wipe_system
from config import HOST, USER, PASSWORD, DB_NAME, BOT_TOKEN, ADMIN_IDS
from pso import bee_algorithm
import psycopg2

# ================= Подключение к боту =================
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
# ======================================================


# ================= Хранение данных ====================
accept_wishes = {0: True}
users_selected_month = {}
users_selected_days = {}
users_vacation_count = {}
days_in_month = {'январь': 31, 'февраль': 28, 'март': 31, 'апрель': 30, 'май': 31, 'июнь': 30, 'июль': 31, 'август': 31,
                 'сентябрь': 30, 'октябрь': 31, 'ноябрь': 30, 'декабрь': 31}
# ======================================================


# Хэндлер на команду /start. Начало общения с ботом.
@dp.message_handler(commands="start")
async def cmd_start(message: types.Message):
    inline_keyboard = types.InlineKeyboardMarkup()
    inline_button1 = types.InlineKeyboardButton("Начать планирование", callback_data="start_button")
    inline_button2 = types.InlineKeyboardButton("Мои отпуска", callback_data="my_vacations_button")
    inline_keyboard.add(inline_button1)
    inline_keyboard.add(inline_button2)
    await message.answer("Вас приветствует бот-помощник по планированию отпуска! "
                         "Для планирования дат воспользуйтесь кнопками ниже.", reply_markup=inline_keyboard)


# Хэндлер на команду /apanel. Панель управления для администраторов
@dp.message_handler(commands="apanel")
async def cmd_apanel(message: types.Message):
    is_admin = False
    for admin_id in ADMIN_IDS:
        if admin_id == message.from_user.id:
            is_admin = True
            break
    if is_admin:
        inline_keyboard = types.InlineKeyboardMarkup()
        inline_button1 = types.InlineKeyboardButton("Сменить статус принятия", callback_data="acceptwishes_button")
        inline_button2 = types.InlineKeyboardButton("Оптимизировать пожелания", callback_data="managewishes_button")
        inline_button3 = types.InlineKeyboardButton("Ежегодная очистка", callback_data="truncate_button")
        inline_keyboard.add(inline_button1)
        inline_keyboard.add(inline_button2)
        inline_keyboard.add(inline_button3)
        await message.answer("Вы открыли панель управления ботом.", reply_markup=inline_keyboard)


# Хэндлер на команду /iamanewemployee2023. Команда для регистрации нового сотрудника.
@dp.message_handler(commands="iamanewemployee2023")
async def iamanewemployee2023(message: types.Message):
    await iamanewemployee(message)


# Ответное действие на нажатие кнопки truncate_button
@dp.callback_query_handler(text="truncate_button")
async def button_truncate(call: types.CallbackQuery):
    await wipe_system()
    inline_keyboard = types.InlineKeyboardMarkup()
    inline_button1 = types.InlineKeyboardButton("В начало", callback_data="back")
    inline_keyboard.add(inline_button1)
    await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    await call.message.answer("Даты отпусков очищены, количество неотгуленных отпусков пополнено у всех сотрудников.", reply_markup=inline_keyboard)


# Ответное действие на нажатие кнопки acceptwishes_button
@dp.callback_query_handler(text="acceptwishes_button")
async def button_acceptwishes(call: types.CallbackQuery):
    inline_keyboard = types.InlineKeyboardMarkup()
    inline_button1 = types.InlineKeyboardButton("В начало", callback_data="back")
    inline_keyboard.add(inline_button1)
    await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    if accept_wishes[0]:
        accept_wishes[0] = False
        await call.message.answer("Сбор пожеланий отключен.", reply_markup=inline_keyboard)
    else:
        accept_wishes[0] = True
        await call.message.answer("Сбор пожеланий включен.", reply_markup=inline_keyboard)


# Ответное действие на нажатие кнопки managewishes_button
@dp.callback_query_handler(text="managewishes_button")
async def button_managewishes(call: types.CallbackQuery):
    inline_keyboard = types.InlineKeyboardMarkup()
    inline_button1 = types.InlineKeyboardButton("В начало", callback_data="back")
    inline_keyboard.add(inline_button1)
    bee_algorithm()
    await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    await call.message.answer("Алгоритм оптимизации пожеланий отработал успешно", reply_markup=inline_keyboard)


# Ответное действие на нажатие кнопки start_button
@dp.callback_query_handler(text="start_button")
async def send_random_value(call: types.CallbackQuery):
    while True:
        if not accept_wishes[0]:
            inline_keyboard = types.InlineKeyboardMarkup()
            inline_button1 = types.InlineKeyboardButton("В начало", callback_data="back")
            inline_keyboard.add(inline_button1)
            await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
            await call.message.answer("Пожелания на отпуска сейчас не принимаются.", reply_markup=inline_keyboard)
            break
        try:
            connection = psycopg2.connect(host=HOST, user=USER, password=PASSWORD,
                                          database=DB_NAME)  # Установка соединения
            with connection.cursor() as cursor:
                # Запрос для проверки существования работника в бд
                cursor.execute("SELECT EXISTS(SELECT 1 FROM unusedvacs WHERE uuid = %s)", (call.from_user.id,))
                exists = cursor.fetchone()[0]  # Сохранение результатов запроса
                if not exists:
                    await call.message.answer("Вы не являетесь сотрудником компании или же вас нет в базе данных. "
                                              "Обратитесь за помощью к администратору.")
                    break
        except Exception as _ex:
            print('Error - ', _ex)
        finally:
            if connection:
                connection.close()
        keyboard = types.InlineKeyboardMarkup(row_width=3)
        months = ['январь', 'февраль', 'март', 'апрель', 'май', 'июнь', 'июль', 'август', 'сентябрь', 'октябрь',
                  'ноябрь', 'декабрь']
        buttons = [types.InlineKeyboardButton(text=month.capitalize(), callback_data=month) for month in months]
        buttons.append(types.InlineKeyboardButton(text="Назад", callback_data="back"))
        keyboard.add(*buttons)
        await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        await call.message.answer("Выберите месяц для отпуска:", reply_markup=keyboard)
        break


@dp.callback_query_handler(lambda c: c.data in days_in_month.keys())
async def process_month_callback(callback_query: types.CallbackQuery):
    await callback_query.answer()
    month = callback_query.data
    user_id = callback_query.from_user.id
    # Сохранение пары (user_id) - (выбранный месяц)
    if month == 'январь':
        users_selected_month[user_id] = 1
    elif month == 'февраль':
        users_selected_month[user_id] = 2
    elif month == 'март':
        users_selected_month[user_id] = 3
    elif month == 'апрель':
        users_selected_month[user_id] = 4
    elif month == 'май':
        users_selected_month[user_id] = 5
    elif month == 'июнь':
        users_selected_month[user_id] = 6
    elif month == 'июль':
        users_selected_month[user_id] = 7
    elif month == 'август':
        users_selected_month[user_id] = 8
    elif month == 'сентябрь':
        users_selected_month[user_id] = 9
    elif month == 'октябрь':
        users_selected_month[user_id] = 10
    elif month == 'ноябрь':
        users_selected_month[user_id] = 11
    elif month == 'декабрь':
        users_selected_month[user_id] = 12
    date_keyboard = types.InlineKeyboardMarkup(row_width=7)
    days = [str(day) for day in range(1, days_in_month[month] + 1)]
    date_buttons = [types.InlineKeyboardButton(text=day, callback_data=day) for day in days]
    date_buttons.append(types.InlineKeyboardButton(text="Назад", callback_data="back"))
    date_keyboard.add(*date_buttons)
    await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
    await callback_query.message.answer(f"Вы выбрали месяц: {month} \n"
                                        "Выберите дату, с какого числа вы хотите уйти в отпуск:",
                                        reply_markup=date_keyboard)


@dp.callback_query_handler(lambda c: c.data.isdigit())
async def process_date_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    date = callback_query.data
    users_selected_days[user_id] = date
    long_vacation = ''
    medium_vacation = ''
    small_vacation = ''
    try:
        connection = psycopg2.connect(host=HOST, user=USER, password=PASSWORD, database=DB_NAME)  # Установка соединения
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM unusedvacs WHERE uuid = %s", (user_id,))
            rows = cursor.fetchall()  # Храним неиспользованные отгулы конкретного user_id
        for row in rows:
            long_vacation = row[2]
            medium_vacation = row[3]
            small_vacation = row[4]
    except Exception as _ex:
        await callback_query.message.answer("Произошла ошибка. Попробуйте сделать это позднее.")
    finally:
        if connection:
            connection.close()
    await callback_query.answer()
    duration_keyboard = types.InlineKeyboardMarkup(row_width=1)
    # Если у user_id не израсходован конкретный тип отгула, то у него появится кнопка для резервирования этого отгула
    durations = []
    if small_vacation > 0:
        durations.append("1 день")
    if medium_vacation > 0:
        durations.append("7 дней")
    if long_vacation > 0:
        durations.append("14 дней")
    duration_buttons = [types.InlineKeyboardButton(text=duration, callback_data=duration) for duration in durations]
    duration_buttons.append(types.InlineKeyboardButton(text="Назад", callback_data="back"))
    duration_keyboard.add(*duration_buttons)
    await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
    await callback_query.message.answer(f"Вы выбрали дату: {date} \n"
                                        "Выберите длительность отпуска:", reply_markup=duration_keyboard)


# Ответное действие на нажатие кнопки выбора длительности отпуска
@dp.callback_query_handler(lambda c: c.data in ["1 день", "7 дней", "14 дней"])
async def process_duration_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    duration = callback_query.data.split()[0]
    # Переопределение длины отпуска в значение необходимое для базы данных
    if duration == '14':
        duration = 'longvacation'
    elif duration == '7':
        duration = 'mediumvacation'
    elif duration == '1':
        duration = 'smallvacation'

    if duration == 'smallvacation':
        await assign_final_smallvacation(user_id, users_selected_days[user_id], users_selected_month[user_id])
    else:
        await assign_vacation(user_id, duration, users_selected_days[user_id], users_selected_month[user_id])
    await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
    inline_keyboard = types.InlineKeyboardMarkup()
    inline_button1 = types.InlineKeyboardButton("Оставить пожелание", callback_data="start_button")
    inline_keyboard.add(inline_button1)
    await callback_query.message.answer("Вы оставили своё пожелание о дате отгула. Желаете оставить больше пожеланий?",
                                        reply_markup=inline_keyboard)


# Ответное действие на нажатие кнопки my_vacations_button. Выдает информацию человеку о его отпусках и отгулах.
@dp.callback_query_handler(text="my_vacations_button")
async def my_vacations_show(call: types.CallbackQuery):
    returnmsg = ""
    try:
        connection = psycopg2.connect(host=HOST, user=USER, password=PASSWORD,
                                      database=DB_NAME)  # Установка соединения  # Установка соединения
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM unusedvacs WHERE uuid = %s", (call.from_user.id,))
            rows = cursor.fetchall()  # Храним данные о неотгуленных отпусках конкретного user.id
        for row in rows:
            returnmsg += "Найденная о вас информация:\n\n"
            returnmsg += f"Неотгулено 14-дневных отпусков : {row[2]}\n"
            returnmsg += f"Неотгулено 7-дневных отпусков : {row[3]}\n"
            returnmsg += f"Неотгулено одиночных дней : {row[4]}\n\n"
    except Exception as _ex:
        await call.message.answer("Произошла ошибка. Попробуйте сделать это позднее.")
    finally:
        if connection:
            connection.close()
    try:
        connection = psycopg2.connect(host=HOST, user=USER, password=PASSWORD,
                                      database=DB_NAME)  # Установка соединения  # Установка соединения
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM wishes WHERE uuid = %s", (call.from_user.id,))
            tables = cursor.fetchall()  # Храним данные о неотгуленных отпусках конкретного user.id
        inline_keyboard = types.InlineKeyboardMarkup(row_width=2)
        inline_buttons = []
        for table in tables:
            returnmsg += f"{table[0]}) Предварительный отгул с {table[3]}.{table[4]}\n"
            days_vacation = ''
            if table[2] == 'longvacation':
                days_vacation += '14'
            elif table[2] == 'mediumvacation':
                days_vacation += '7'
            elif table[2] == 'smallvacation':
                days_vacation += '1'
            returnmsg += f"    Длительностью {days_vacation} дней\n\n"
            inline_buttons.append(
                types.InlineKeyboardButton(text=f"Удалить №{table[0]}", callback_data=f"{table[0]}_updatestart"))
        returnmsg += "\n"
        inline_buttons.append(types.InlineKeyboardButton(text="Назад", callback_data="back"))
        inline_keyboard.add(*inline_buttons)
    except Exception as _ex:
        await call.message.answer("Произошла ошибка. Попробуйте сделать это позднее.")
    finally:
        if connection:
            connection.close()
    try:
        connection = psycopg2.connect(host=HOST, user=USER, password=PASSWORD,
                                      database=DB_NAME)  # Установка соединения  # Установка соединения
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM finaldates WHERE uuid = %s", (call.from_user.id,))
            tables = cursor.fetchall()  # Храним данные о неотгуленных отпусках конкретного user.id
        for table in tables:
            returnmsg += f"Запланирован отгул с {table[2]}\n"
            returnmsg += f"   и продлится до {table[3]}\n\n"
        await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        await call.message.answer(returnmsg, reply_markup=inline_keyboard)
    except Exception as _ex:
        await call.message.answer("Произошла ошибка. Попробуйте сделать это позднее.")
    finally:
        if connection:
            connection.close()


@dp.callback_query_handler(lambda c: c.data[c.data.find('_') + 1:] == 'updatestart')
async def update_start(call: types.CallbackQuery):
    user_id = call.from_user.id
    vacation_type = ''
    editing_vacationid = call.data.split('_')[0]
    try:
        connection = psycopg2.connect(host=HOST, user=USER, password=PASSWORD,
                                      database=DB_NAME)  # Установка соединения  # Установка соединения
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM wishes WHERE vacationid = %s", (editing_vacationid,))
            rows = cursor.fetchall()  # Храним данные о неотгуленных отпусках конкретного user.id
        for row in rows:
            vacation_type += row[2]
    except Exception as _ex:
        await call.message.answer("Произошла ошибка. Попробуйте сделать это позднее.")
    finally:
        if connection:
            connection.close()
    try:
        connection = psycopg2.connect(host=HOST, user=USER, password=PASSWORD, database=DB_NAME)  # Установка соединения
        with connection.cursor() as cursor:
            # Запрос удаления строки по id отпуска
            cursor.execute("DELETE FROM wishes WHERE vacationid = %s;"
                           "UPDATE unusedvacs SET {} = {} + 1 WHERE uuid = %s;".format(vacation_type, vacation_type),
                           (editing_vacationid, user_id))
            connection.commit()  # Исполнение запроса
    except Exception as _ex:
        print('Error - ', _ex)
    finally:
        if connection:
            connection.close()
    inline_keyboard = types.InlineKeyboardMarkup()
    inline_button1 = types.InlineKeyboardButton("В начало", callback_data="back")
    inline_keyboard.add(inline_button1)
    await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    await call.message.answer('Пожелание удалено.', reply_markup=inline_keyboard)


# Ответное действие на нажатие кнопки back
@dp.callback_query_handler(lambda c: c.data == 'back')
async def process_back_callback(callback_query: types.CallbackQuery):
    await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
    await cmd_start(callback_query.message)


# Запуск бота
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
