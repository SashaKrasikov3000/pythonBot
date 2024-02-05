import telebot
import pymysql
import config
import requests

bot = telebot.TeleBot(config.token)
searching = False

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
        result = search(msg)
        if result == -1:
            bot.send_message(msg.chat.id, "Ошибка: подключение прервано")
        else:
            if len(result) > 0:
                bot.send_message(msg.chat.id, "Вот что я нашел:")
                for part in result:     # Вывод результата
                    try:    # Проверка есть ли картинка у товара
                        bot.send_photo(msg.chat.id, f"https://spb.camsparts.ru/files/shop_preview/{part[9]}.jpg", caption=f"{part[0]}\nКод: {part[9]}\nЦена: {part[1]} рублей\nКоличество:\nСПБ Парнас: {part[2]}, Москва: {part[3]}, Ставрополь: {part[4]}, Великий Новгород: {part[5]}, Краснодар: {part[6]}, Тюмень: {part[7]}, Сургут: {part[8]}")
                    except telebot.apihelper.ApiTelegramException as ex:    # Если нет, вывести только текст
                        bot.send_message(msg.chat.id, f"{part[0]}\nКод: {part[9]}\nЦена: {part[1]} рублей\nКоличество:\nСПБ Парнас: {part[2]}, Москва: {part[3]}, Ставрополь: {part[4]}, Великий Новгород: {part[5]}, Краснодар: {part[6]}, Тюмень: {part[7]}, Сургут: {part[8]}")
            else:
                bot.send_message(msg.chat.id, "Ничего не найдено")
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
        print("Connected")
        cursor = conn.cursor()
        cursor.execute(f"SELECT name, price, amount_warehouse1, amount_warehouse2, amount_warehouse3, amount_warehouse4, amount_warehouse5, amount_warehouse6, amount_warehouse7, code from shop_products WHERE article = {msg.text} OR code = {msg.text} OR text LIKE '%{msg.text}%'")   # 3948095 {f'article = {msg.text}' if len(msg.text) > 5 else f'code = {*8-len(msg.text) + msg.text}'}
        out = cursor.fetchall()
        conn.close()
        for row in out:
            print(row)
        return out

    except Exception as ex:     # Если ошибка в подключении
        print("Connection refused: ", ex)
        return -1

bot.infinity_polling()
