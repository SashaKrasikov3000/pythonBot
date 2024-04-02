from telebot import telebot, types
import pymysql
import config
import time
from datetime import datetime, timezone, timedelta
import sqlite3
import logging

time.sleep(5)
bot = telebot.TeleBot(config.token)
parts_list = []  # список для хранения данных о запчастях
# для вывода в callback_part_details

logging.basicConfig(
    level=logging.INFO,
    filename="error_log.txt",
    filemode="a",
    format="%(levelname)s: %(message)s     %(asctime)s"
)
logging.info("\n\n-----STARTING BOT-----")


@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.data.isnumeric():  # Если передан индекс запчасти в массиве
        part, select_index, msg = parts_list[int(call.data)]
        display_info(part, select_index, msg.chat.id, msg.text)
    # Настройки бота. e(enable) или d(disable) + номер настройки
    elif call.data[0] in ['e', 'd'] and call.data[1].isnumeric():
        username = call.data[2:]
        settings = sqlite_query(
            f"SELECT settings FROM users WHERE username = '{username}'"
        )[0][0]
        if call.data[0] == "e":
            sqlite_query(
                "UPDATE users"
                "SET settings = " + settings[:int(call.data[1])]
                + '1' + settings[int(call.data[1])+1:]
                + f"WHERE username = '{username}'"
            )
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(
                types.InlineKeyboardButton(
                    text="Button mode: On",
                    callback_data="d0"+username,
                )
            )
            bot.edit_message_text(
                "Настройки",
                call.message.chat.id, call.message.message_id,
                reply_markup=keyboard,
            )
        else:
            sqlite_query(
                "UPDATE users"
                "SET settings = " + settings[0][0][:int(call.data[1])]
                + '0' + settings[0][0][int(call.data[1])+1:]
                + f"WHERE username = '{username}'"
            )
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(
                types.InlineKeyboardButton(
                    text="Button mode: Off",
                    callback_data="e0"+username,
                )
            )
            bot.edit_message_text(
                "Настройки",
                call.message.chat.id, call.message.message_id,
                reply_markup=keyboard,
            )


@bot.message_handler(commands=["start"])
def greet(msg):
    bot.send_message(
        msg.chat.id,
        "Напишите артикул или код товара. Например: 3948095 или 1221",
    )
    if not sqlite_query(
            "SELECT *"
            "FROM users"
            f"WHERE username = '{msg.from_user.username}'"
    ):
        sqlite_query(
            "INSERT INTO users (username, is_admin, settings)"
            f"VALUES ('{msg.from_user.username}', 0, '00000')"
        )


@bot.message_handler(commands=["settings"])
def settings(msg):
    if not sqlite_query(
            "SELECT * FROM users WHERE username = '{msg.from_user.username}'"
    ):
        sqlite_query(
            "INSERT INTO users (username, is_admin, settings) "
            f"VALUES ('{msg.from_user.username}', 0, '00000')"
        )
    keyboard = types.InlineKeyboardMarkup()
    settings = sqlite_query(
        "SELECT settings "
        "FROM users "
        f"WHERE username = '{msg.from_user.username}'"
    )[0][0]
    keyboard.add(types.InlineKeyboardButton(
        text=f"Button mode: {'On' if settings[0] == '1' else 'Off'}",
        callback_data=('d' if settings[0] == '1' else 'e')
        + '0' + msg.from_user.username)
    )
    bot.send_message(msg.chat.id, "Настройки", reply_markup=keyboard)


@bot.message_handler(commands=["log"])     # Получить логи
def admin(msg):
    # Доступ к логам только у админов
    if sqlite_query(
            "SELECT * "
            "FROM users "
            f"WHERE username = '{msg.from_user.username}' and is_admin = 1"
    ):
        output = ""
        # Команда /log errors выводит логи из файла error_log.txt
        if msg.text[5:] == "errors":
            with open("error_log.txt", "r") as f:
                output = f.read()
        # Команда /log errors clear удаляет логи errors_log.txt
        elif msg.text[5:] == "errors clear":
            with open("error_log.txt", "w") as f:
                f.close()
                output = "Error logs cleared"
        else:
            try:
                # После /log можно указать свой запрос
                result = sqlite_query(
                    'SELECT * FROM log' if len(msg.text) == 4 else msg.text[4:]
                )
            except sqlite3.OperationalError as ex:
                result = [["Ошибка во время выполнения SQL запроса"]]
                logging.error(ex)
            for i in result:
                if len(msg.text) == 4:  # Если введен просто /log
                    output += f"{i[0]}. " \
                              f"User @{i[1]} " \
                              f"searched {i[2]}" \
                              f" with error: {i[3]}"\
                              if i[3] is not None else " " \
                              f"at {i[4]}\n"
                else:
                    for j in i:
                        output += f"{j}  "
                    output += "\n"
        for i in range(0, len(output), 4095):
            bot.send_message(msg.chat.id, output[i:i + 4095])


# Получение артикула, передача в функцию поиска и обработка
@bot.message_handler(content_types=["text"])
def handle_text(msg):
    global parts_list
    if not sqlite_query(
            f"SELECT * FROM users WHERE username = '{msg.from_user.username}'"
    ):
        sqlite_query(
            f"INSERT INTO users (username, is_admin, settings) "
            f"VALUES ('{msg.from_user.username}', 0, '00000')"
        )
    result, select = search(msg)
    if result == -1:
        bot.send_message(msg.chat.id, "Ошибка при выполнении запроса")
    else:
        if len(result) > 0:
            # Если включен режим кнопок (первая цифра в настройках)
            if sqlite_query(
                    f"SELECT * "
                    f"FROM users "
                    f"WHERE username = '{msg.from_user.username}' "
                    f"and settings LIKE '1____'"
            ):
                keyboard = types.InlineKeyboardMarkup()
                parts_list = []
                # Вывод результата с кнопками
                for part, select_index, i \
                        in zip(result, select, range(len(result))):
                    parts_list.append([part, select_index, msg])
                    keyboard.add(
                        types.InlineKeyboardButton(
                            text=part[0],
                            callback_data=f"{i}"
                        )
                    )
                if len(parts_list) > 1:
                    bot.send_message(
                        msg.chat.id,
                        "Вот что я нашел:", reply_markup=keyboard
                    )
                else:    # Если всего один результат, вывести сразу без кнопки
                    display_info(
                        parts_list[0][0],
                        parts_list[0][1],
                        parts_list[0][2],
                        parts_list[0][3],
                    )
            else:
                # Вывод результата без кнопок
                for part, select_index in zip(result, select):
                    display_info(part, select_index, msg.chat.id, msg.text)
        else:
            bot.send_message(
                msg.chat.id,
                "Ничего не найдено "
                + ("по коду" if len(msg.text) <= 5 else "по артикулу")
            )


def sqlite_query(query):
    print(query)
    logging.info(f"SQL query: {query}")
    con = sqlite3.connect("Camsparts.db")
    cursor = con.cursor()
    result = cursor.execute(query)
    if any([i in query for i in ["INSERT", "UPDATE", "DELETE"]]):
        con.commit()
    result = result.fetchall()
    con.close()
    return result


def display_info(part, select_index, chat_id, msg_text):    # Вывод информации
    try:  # Проверка есть ли картинка у товара
        bot.send_photo(
            chat_id,
            f"https://spb.camsparts.ru/files/shop_preview/{part[9]}.jpg",
            caption=f"{part[0]}\n"
                    f"Артикул: "
                    + ('*' + part[10] + '*' + "\n")
            if select_index == -2 else part[10] + "\n"
                    "Код: "
                    + ('*' + part[9] + '*' + "\n")
            if select_index == -3 else part[9] + "\n"
                    "Кросс номера: " + (part[11][:select_index]
                                        + '*' + msg_text.upper() + '*'
                                        + part[11][select_index+len(msg_text):]
                                        + "\n")
            if select_index >= 0 else part[11] + "\n"
                    f"Цена розничная: {part[1]}₽\n"
                    f"Цена оптовая: {part[12]}₽\n"
                    f"Количество:\n"
                    f"СПБ Парнас: {part[2]}, Ставрополь: {part[3]}, "
                    f"Сургут: {part[4]}, Краснодар: {part[5]},"
                    f"Тюмень: {part[6]}, Великий Новгород: {part[8]}",
            parse_mode="Markdown"
        )
    # Если нет, вывести только текст
    except telebot.apihelper.ApiTelegramException:
        bot.send_message(
            chat_id,
            f"{part[0]}\n"
            f"Артикул: "
            + ('*' + part[10] + '*' + "\n")
            if select_index == -2 else part[10] + "\n"
            "Код: "
            + ('*' + part[9] + '*' + "\n")
            if select_index == -3 else part[9] + "\n"
            "Кросс номера: " + (part[11][:select_index]
                                + '*' + msg_text.upper() + '*'
                                + part[11][select_index+len(msg_text):]
                                + "\n")
            if select_index >= 0 else part[11] + "\n"
            f"Цена розничная: {part[1]}₽\n"
            f"Цена оптовая: {part[12]}₽\n"
            f"Количество:\n"
            f"СПБ Парнас: {part[2]}, Ставрополь: {part[3]}, "
            f"Сургут: {part[4]}, Краснодар: {part[5]},"
            f"Тюмень: {part[6]}, Великий Новгород: {part[8]}",
            parse_mode="Markdown")


# Функция для подключения к базе данных и получения информации
def search(msg):
    try:
        conn = pymysql.connect(
            host=config.host,
            port=config.port,
            user=config.user,
            password=config.password,
            database=config.database
        )

        print("Connected       "+msg.text+"      "+time.ctime())
        sqlite_query(
            f"INSERT INTO log (username, request, time) "
            f"VALUES ('{msg.from_user.username}', "
            f"'{msg.text}', '"
            + str(datetime.now(timezone.utc)+timedelta(hours=3))[:-13]
            + "')"
        )
        logging.info(
            f"User @{msg.from_user.username} "
            f"searched {msg.text} "
            f"at {str(datetime.now(timezone.utc)+timedelta(hours=3))[:-13]}\n"
        )

        cursor = conn.cursor()
        # Массив в котором хранится то, что нужно выделить
        # жирным шрифтом для каждой детали.
        # -3 - выделить код, -2 - выделить артикул,
        # число - индекс буквы, с которой начинается
        # выделяемое слово в кросс номерах
        select = []
        if len(msg.text) <= 5 and msg.text.isnumeric():
            cursor.execute(
                "SELECT name, price, amount_warehouse1, amount_warehouse2, "
                "amount_warehouse3, amount_warehouse4, amount_warehouse5, "
                "amount_warehouse6, amount_warehouse7, code, article, "
                f"text, price2 from shop_products WHERE code = {msg.text}"
            )
            out = cursor.fetchall()
            conn.close()
            for i in range(len(out)):
                select.append(-3)
        # Фильтр для избежания SQL инъекции
        elif not any(
                [i in msg.text for i in ["'", '"', "%", ",", "#", "--", ";"]]
        ):
            cursor.execute(
                "SELECT name, price, amount_warehouse1, amount_warehouse2, "
                "amount_warehouse3, amount_warehouse4, amount_warehouse5, "
                "amount_warehouse6, amount_warehouse7, code, article, "
                f"text, price2 from shop_products "
                f"WHERE article = '{msg.text}' OR text LIKE '%{msg.text}%'"
            )
            out = cursor.fetchall()
            conn.close()
            for i in range(len(out)):
                # Если найдено по артикулу, выделить его
                if out[i][10] == msg.text:
                    select.append(-2)
                else:  # Если найдено по кросс номеру, выделить его
                    select.append(out[i][11].find(msg.text.upper()))
        else:   # Если запрос не подходит под артикул или код, выдать ошибку
            return -1, 0

        return out, select

    except Exception as ex:     # Если ошибка
        print("Error: ", ex)
        logging.error("Exception in search(): ", exc_info=True)
        sqlite_query(
            f"INSERT INTO log (username, request, exception, time) "
            f"VALUES ({msg.from_user.username}, {msg.text}, {ex}, "
            f"{str(datetime.now(timezone.utc) + timedelta(hours=3))[:-13]})"
        )
        return -1, 0


# print(sqlite_query("DROP TABLE users"))
# print(sqlite_query("CREATE TABLE users (id INTEGER, username TEXT, "
#       + "is_admin BOOLEAN, settings TEXT, PRIMARY KEY (id))"))
# print(sqlite_query("INSERT INTO users (username, is_admin, settings) "
#       + "VALUES ('SashaKrasikov', 1, '00000')"))
# print(sqlite_query("UPDATE users SET is_admin = 1 "
#       + "WHERE username = 'SashaKrasikov'"))
print(sqlite_query("SELECT * FROM users"))

bot.infinity_polling()
