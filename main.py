from telebot import *
import pymysql
import config
import time
from datetime import datetime, timezone, timedelta
import requests
import sqlite3

time.sleep(5)
bot = telebot.TeleBot(config.token)
button_mode = {"SashaKrasikov": False}    # Режим для вывода результата с кнопками
parts_list = []    # список для хранения данных о запчастях для вывода в callback_part_details (оно не влезает в callback_data)

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    global button_mode
    if call.data.isnumeric():   # Если передано число (индекс запчасти в массиве)
        part, select_index, msg = parts_list[int(call.data)]
        try:  # Проверка есть ли картинка у товара
            bot.send_photo(msg.chat.id, f"https://spb.camsparts.ru/files/shop_preview/{part[9]}.jpg", caption=f"{part[0]}\nАртикул: {'*' + part[10] + '*' if select_index == -2 else part[10]}\nКод: {'*' + part[9] + '*' if select_index == -3 else part[9]}\nКросс номера: {part[11][:select_index] + '*' + msg.text.upper() + '*' + part[11][select_index + len(msg.text):] if select_index >= 0 else part[11]}\nЦена: {part[1]} рублей\nКоличество:\nСПБ Парнас: {part[2]}, Ставрополь: {part[3]}, Сургут: {part[4]}, Краснодар: {part[5]}, Тюмень: {part[6]}, Великий Новгород: {part[8]}", parse_mode="Markdown")
        except telebot.apihelper.ApiTelegramException as ex:  # Если нет, вывести только текст
            bot.send_message(msg.chat.id, f"{part[0]}\nАртикул: {'*' + part[10] + '*' if select_index == -2 else part[10]}\nКод: {'*' + part[9] + '*' if select_index == -3 else part[9]}\nКросс номера: {part[11][:select_index] + '*' + msg.text.upper() + '*' + part[11][select_index + len(msg.text):] if select_index >= 0 else part[11]}\nЦена: {part[1]} рублей\nКоличество:\nСПБ Парнас: {part[2]}, Ставрополь: {part[3]}, Сургут: {part[4]}, Краснодар: {part[5]}, Тюмень: {part[6]}, Великий Новгород: {part[8]}", parse_mode="Markdown")
    elif call.data[0] in ['e', 'd'] and call.data[1].isnumeric():   # Настройки бота. e(enable) или d(disable) + номер настройки
        if call.data[1] == "0":
            username = call.data[2:]
            button_mode[username] = True if call.data[0] == "e" else False
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton(text=f"Button mode: {button_mode[username]}", callback_data=f"{('d' if button_mode[username] else 'e') + '0'}"))
            bot.edit_message_text("Настройки", call.message.chat.id, call.message.message_id, reply_markup=keyboard)

@bot.message_handler(commands=["start"])
def greet(msg):
    bot.send_message(msg.chat.id, "Напишите артикул или код товара. Например: 3948095 или 1221")
    if msg.from_user.username not in button_mode:
        button_mode[msg.from_user.username] = False


@bot.message_handler(commands=["settings"])
def settings(msg):
    if msg.from_user.username not in button_mode:
        button_mode[msg.from_user.username] = False
    print(button_mode)
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text=f"Button mode: {button_mode[msg.from_user.username]}", callback_data=f"{('d' if button_mode[msg.from_user.username] else 'e')+'0'+msg.from_user.username}"))
    bot.send_message(msg.chat.id, "Настройки", reply_markup=keyboard)

@bot.message_handler(commands=["log"])     # Получить логи
def admin(msg):
    if msg.from_user.username == "SashaKrasikov":
        with open("log.txt", 'r') as log:
            info = log.read()
            for i in range(0, len(info), 4095):
                bot.send_message(msg.chat.id, info[i:i + 4095])


@bot.message_handler(content_types=["text"])    # Получение артикула, передача в функцию поиска и обработка
def handle_text(msg):
    global parts_list
    result, select = search(msg)
    if result == -1:
        bot.send_message(msg.chat.id, "Ошибка при выполнении запроса")
    else:
        if len(result) > 0:
            if button_mode[msg.from_user.username]:
                keyboard = types.InlineKeyboardMarkup()
                parts_list = []
                for part, select_index, i in zip(result, select, [i for i in range(len(result))]):    # Вывод результата с кнопками
                    print(f"{part} , {select_index} , {msg.chat.id} , {msg.text}")
                    parts_list.append([part, select_index, msg])
                    keyboard.add(types.InlineKeyboardButton(text=part[0], callback_data=f"{i}"))
                if len(parts_list) > 1:    # Если всего один результат, вывести сразу без кнопки
                    bot.send_message(msg.chat.id, "Вот что я нашел:", reply_markup=keyboard)
                else:
                    display_info(parts_list[0][0], parts_list[0][1], parts_list[0][2], parts_list[0][3])
            else:
                if msg.from_user.username not in button_mode:
                    button_mode[msg.from_user.username] = False
                for part, select_index in zip(result, select):    # Вывод результата без кнопок
                    display_info(part, select_index, msg.chat.id, msg.text)
        else:
            bot.send_message(msg.chat.id, "Ничего не найдено "+("по коду" if len(msg.text) <= 5 else "по артикулу"))


def display_info(part, select_index, chat_id, msg_text):    # Вывод информации
    try:  # Проверка есть ли картинка у товара
        bot.send_photo(chat_id, f"https://spb.camsparts.ru/files/shop_preview/{part[9]}.jpg", caption=f"{part[0]}\nАртикул: {'*' + part[10] + '*' if select_index == -2 else part[10]}\nКод: {'*' + part[9] + '*' if select_index == -3 else part[9]}\nКросс номера: {part[11][:select_index] + '*' + msg_text.upper() + '*' + part[11][select_index + len(msg_text):] if select_index >= 0 else part[11]}\nЦена розничная: {part[1]}₽\nЦена оптовая: {part[12]}₽\nКоличество:\nСПБ Парнас: {part[2]}, Ставрополь: {part[3]}, Сургут: {part[4]}, Краснодар: {part[5]}, Тюмень: {part[6]}, Великий Новгород: {part[8]}", parse_mode="Markdown")
    except telebot.apihelper.ApiTelegramException as ex:  # Если нет, вывести только текст
        bot.send_message(chat_id, f"{part[0]}\nАртикул: {'*' + part[10] + '*' if select_index == -2 else part[10]}\nКод: {'*' + part[9] + '*' if select_index == -3 else part[9]}\nКросс номера: {part[11][:select_index] + '*' + msg_text.upper() + '*' + part[11][select_index + len(msg_text):] if select_index >= 0 else part[11]}\nЦена розничная: {part[1]}₽\nЦена оптовая: {part[12]}₽\nКоличество:\nСПБ Парнас: {part[2]}, Ставрополь: {part[3]}, Сургут: {part[4]}, Краснодар: {part[5]}, Тюмень: {part[6]}, Великий Новгород: {part[8]}", parse_mode="Markdown")


def search(msg):    # Функция для подключения к базе данных и получения информации
    try:
        conn = pymysql.connect(
            host=config.host,
            port=config.port,
            user=config.user,
            password=config.password,
            database=config.database
        )
        print("Connected       "+msg.text+"      "+time.ctime())
        with open("log.txt", "a") as log:
            log.write(f"{str(datetime.now(timezone.utc)+timedelta(hours=3))[:-13]}    User @{msg.from_user.username} searched {msg.text}\n")
        cursor = conn.cursor()
        select = []     # Массив в котором хранится то, что нужно выделить жирным шрифтом для каждой детали. -3 - выделить код, -2 - выделить артикул, число - индекс буквы, с которой начинается выделяемое слово в кросс номерах. Костыль, но нормального способа я не придумал
        if len(msg.text) <= 5 and msg.text.isnumeric():
            cursor.execute(f"SELECT name, price, amount_warehouse1, amount_warehouse2, amount_warehouse3, amount_warehouse4, amount_warehouse5, amount_warehouse6, amount_warehouse7, code, article, text, price2 from shop_products WHERE code = {msg.text}")
            out = cursor.fetchall()
            conn.close()
            for i in range(len(out)):
                select.append(-3)
        elif not any([i in msg.text for i in ["'", '"', "%", ",", "#", "--", ";"]]):    # Фильтр для избежания SQL инъекции
            cursor.execute(f"SELECT name, price, amount_warehouse1, amount_warehouse2, amount_warehouse3, amount_warehouse4, amount_warehouse5, amount_warehouse6, amount_warehouse7, code, article, text, price2 from shop_products WHERE article = '{msg.text}' OR text LIKE '%{msg.text}%'")
            out = cursor.fetchall()
            conn.close()
            for i in range(len(out)):
                if out[i][10] == msg.text:  # Если найдено по артикулу, выделить его
                    select.append(-2)
                else:  # Если найдено по кросс номеру, выделить его
                    select.append(out[i][11].find(msg.text.upper()))
        else:   # Если запрос не подходит под артикул или код, выдать ошибку
            return -1, 0

        return out, select

    except Exception as ex:     # Если ошибка
        print("Error: ", ex)
        with open("log.txt", "a") as log:
            log.write(f"{str(datetime.now(timezone.utc)+timedelta(hours=3))[:-13]}    User @{msg.from_user.username} searched {msg.text}    {ex}\n")
        return -1, 0


bot.infinity_polling()
