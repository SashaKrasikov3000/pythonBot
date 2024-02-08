import telebot
import pymysql
import config
import time
import requests

bot = telebot.TeleBot(config.token)
searching = True
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


@bot.message_handler(content_types=["text"])    # Получение артикула, передача в функцию поиска и обработка
def handle_text(msg):
    if searching:
        result, select = search(msg)
        if result == -1:
            bot.send_message(msg.chat.id, "Ошибка при выполнении запроса")
        else:
            if len(result) > 0:
                bot.send_message(msg.chat.id, "Вот что я нашел:")
                for part, select_index in zip(result, select):     # Вывод результата
                    print(part, select_index)
                    try:    # Проверка есть ли картинка у товара
                        bot.send_photo(msg.chat.id, f"https://spb.camsparts.ru/files/shop_preview/{part[9]}.jpg", caption=f"{part[0]}\nАртикул: {'*'+part[10]+'*' if select_index == -2 else part[10]}\nКод: {'*'+part[9]+'*' if select_index == -3 else part[9]}\nКросс номера: {part[11][:part[11].find(msg.text)] + '*' + msg.text + '*' + part[11][part[11].find(msg.text)+len(msg.text):] if select_index > 0 else part[11]}\nЦена: {part[1]} рублей\nКоличество:\nСПБ Парнас: {part[2]}, Москва: {part[3]}, Ставрополь: {part[4]}, Великий Новгород: {part[5]}, Краснодар: {part[6]}, Тюмень: {part[7]}, Сургут: {part[8]}", parse_mode="Markdown")
                    except telebot.apihelper.ApiTelegramException as ex:    # Если нет, вывести только текст
                        bot.send_message(msg.chat.id, f"{part[0]}\nАртикул: {'*'+part[10]+'*' if select_index == -2 else part[10]}\nКод: {'*'+part[9]+'*' if select_index == -3 else part[9]}\nКросс номера: {part[11][:part[11].find(msg.text)] + '*' + msg.text + '*' + part[11][part[11].find(msg.text)+len(msg.text):] if select_index > 0 else part[11]}\nЦена: {part[1]} рублей\nКоличество:\nСПБ Парнас: {part[2]}, Москва: {part[3]}, Ставрополь: {part[4]}, Великий Новгород: {part[5]}, Краснодар: {part[6]}, Тюмень: {part[7]}, Сургут: {part[8]}", parse_mode="Markdown")
            else:
                bot.send_message(msg.chat.id, "Ничего не найдено "+("по коду" if len(msg.text) <= 5 else "по артикулу"))
    else:
        bot.send_message(msg.chat.id, "Чтобы найти деталь используй /find")


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
                    select.append(out[i][11].find(msg.text))

        conn.close()
        for row in out:
            print(row)
        return out, select

    except Exception as ex:     # Если ошибка
        print("Error: ", ex)
        return -1


bot.infinity_polling()
