from telebot import *
import pymysql
import config
import time
from datetime import datetime, timezone, timedelta
import requests

time.sleep(5)
bot = telebot.TeleBot(config.token)
searching = True
button_mode = False    # Режим для вывода результата с кнопками
parts_list = []    # список для хранения данных о запчастях для вывода в callback_part_details (оно не влезает в callback_data)

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    global button_mode
    if call.data.isnumeric():   # Если передано число (индекс запчасти в массиве)
        part, select_index, chat_id, msg_text = parts_list[int(call.data)]
        try:  # Проверка есть ли картинка у товара
            bot.send_photo(chat_id, f"https://spb.camsparts.ru/files/shop_preview/{part[9]}.jpg", caption=f"{part[0]}\nАртикул: {'*' + part[10] + '*' if select_index == -2 else part[10]}\nКод: {'*' + part[9] + '*' if select_index == -3 else part[9]}\nКросс номера: {part[11][:select_index] + '*' + msg_text.upper() + '*' + part[11][select_index + len(msg_text):] if select_index >= 0 else part[11]}\nЦена: {part[1]} рублей\nКоличество:\nСПБ Парнас: {part[2]}, Ставрополь: {part[3]}, Сургут: {part[4]}, Краснодар: {part[5]}, Тюмень: {part[6]}, Великий Новгород: {part[8]}", parse_mode="Markdown")
        except telebot.apihelper.ApiTelegramException as ex:  # Если нет, вывести только текст
            bot.send_message(chat_id, f"{part[0]}\nАртикул: {'*' + part[10] + '*' if select_index == -2 else part[10]}\nКод: {'*' + part[9] + '*' if select_index == -3 else part[9]}\nКросс номера: {part[11][:select_index] + '*' + msg_text.upper() + '*' + part[11][select_index + len(msg_text):] if select_index >= 0 else part[11]}\nЦена: {part[1]} рублей\nКоличество:\nСПБ Парнас: {part[2]}, Ставрополь: {part[3]}, Сургут: {part[4]}, Краснодар: {part[5]}, Тюмень: {part[6]}, Великий Новгород: {part[8]}", parse_mode="Markdown")
    elif call.data[0] in ['e', 'd'] and call.data[1].isnumeric():   # Настройки бота. e(enable) или d(disable) + номер настройки
        if call.data[1] == "0":
            button_mode = True if call.data[0] == "e" else False
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton(text=f"Button mode: {button_mode}", callback_data=f"{('d' if button_mode else 'e') + '0'}"))
            bot.edit_message_text("Настройки", call.message.chat.id, call.message.message_id, reply_markup=keyboard)

@bot.message_handler(commands=["start"])
def greet(msg):
    bot.send_message(msg.chat.id, "Привет, я помогу найти информацию о запчастях по их артикулу. Напиши /find для поиска")


@bot.message_handler(commands=["find"])     # Запустить поиск
def enable_searching(msg):
    global searching
    searching = True
    bot.send_message(msg.chat.id, "Теперь пиши мне артикулы, а я буду искать по ним информацию. Чтобы прекратить напиши /stop")


@bot.message_handler(commands=["stop"])     # Остановка поиска
def stop_searching(msg):
    global searching
    searching = False
    bot.send_message(msg.chat.id, "Остановка")


@bot.message_handler(commands=["settings"])
def settings(msg):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text=f"Button mode: {button_mode}", callback_data=f"{('d' if button_mode else 'e')+'0'}"))
    bot.send_message(msg.chat.id, "Настройки", reply_markup=keyboard)

@bot.message_handler(commands=["log"])     # Получить логи
def admin(msg):
    if msg.from_user.username == "SashaKrasikov":
        with open("log.txt", 'r') as log:
            bot.send_message(msg.chat.id, log.read())


@bot.message_handler(content_types=["text"])    # Получение артикула, передача в функцию поиска и обработка
def handle_text(msg):
    global parts_list
    if searching:
        result, select = search(msg)
        if result == -1:
            bot.send_message(msg.chat.id, "Ошибка при выполнении запроса")
        else:
            if len(result) > 0:
                if button_mode:
                    keyboard = types.InlineKeyboardMarkup()
                    parts_list = []
                    for part, select_index, i in zip(result, select, [i for i in range(len(result))]):    # Вывод результата с кнопками
                        print(f"{part} , {select_index} , {msg.chat.id} , {msg.text}")
                        parts_list.append([part, select_index, msg.chat.id, msg.text])
                        keyboard.add(types.InlineKeyboardButton(text=part[0], callback_data=f"{i}"))
                    if len(parts_list) > 1:    # Если всего один результат, вывести сразу без кнопки
                        bot.send_message(msg.chat.id, "Вот что я нашел:", reply_markup=keyboard)
                    else:
                        display_info(parts_list[0][0], parts_list[0][1], parts_list[0][2], parts_list[0][3])
                else:
                    for part, select_index in zip(result, select):    # Вывод результата без кнопок
                        display_info(part, select_index, msg.chat.id, msg.text)
            else:
                bot.send_message(msg.chat.id, "Ничего не найдено "+("по коду" if len(msg.text) <= 5 else "по артикулу"))
    else:
        bot.send_message(msg.chat.id, "Чтобы найти деталь используй /find")


def display_info(part, select_index, chat_id, msg_text):    # Вывод информации
    try:  # Проверка есть ли картинка у товара
        bot.send_photo(chat_id, f"https://spb.camsparts.ru/files/shop_preview/{part[9]}.jpg", caption=f"{part[0]}\nАртикул: {'*' + part[10] + '*' if select_index == -2 else part[10]}\nКод: {'*' + part[9] + '*' if select_index == -3 else part[9]}\nКросс номера: {part[11][:select_index] + '*' + msg_text.upper() + '*' + part[11][select_index + len(msg_text):] if select_index >= 0 else part[11]}\nЦена: {part[1]} рублей\nКоличество:\nСПБ Парнас: {part[2]}, Ставрополь: {part[3]}, Сургут: {part[4]}, Краснодар: {part[5]}, Тюмень: {part[6]}, Великий Новгород: {part[8]}", parse_mode="Markdown")
    except telebot.apihelper.ApiTelegramException as ex:  # Если нет, вывести только текст
        bot.send_message(chat_id, f"{part[0]}\nАртикул: {'*' + part[10] + '*' if select_index == -2 else part[10]}\nКод: {'*' + part[9] + '*' if select_index == -3 else part[9]}\nКросс номера: {part[11][:select_index] + '*' + msg_text.upper() + '*' + part[11][select_index + len(msg_text):] if select_index >= 0 else part[11]}\nЦена: {part[1]} рублей\nКоличество:\nСПБ Парнас: {part[2]}, Ставрополь: {part[3]}, Сургут: {part[4]}, Краснодар: {part[5]}, Тюмень: {part[6]}, Великий Новгород: {part[8]}", parse_mode="Markdown")


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
        if len(msg.text) <= 5:
            cursor.execute(f"SELECT name, price, amount_warehouse1, amount_warehouse2, amount_warehouse3, amount_warehouse4, amount_warehouse5, amount_warehouse6, amount_warehouse7, code, article, text from shop_products WHERE code = {msg.text}")
            out = cursor.fetchall()
            for i in range(len(out)):
                select.append(-3)
        else:    # Если по коду не найдено, искать по артикулам
            cursor.execute(f"SELECT name, price, amount_warehouse1, amount_warehouse2, amount_warehouse3, amount_warehouse4, amount_warehouse5, amount_warehouse6, amount_warehouse7, code, article, text from shop_products WHERE article = '{msg.text}' OR text LIKE '%{msg.text}%'")
            out = cursor.fetchall()
            for i in range(len(out)):
                if out[i][10] == msg.text:  # Если найдено по артикулу, выделить его
                    select.append(-2)
                else:  # Если найдено по кросс номеру, выделить его
                    select.append(out[i][11].find(msg.text.upper()))

        conn.close()
        return out, select

    except Exception as ex:     # Если ошибка
        print("Error: ", ex)
        return -1


bot.infinity_polling()
