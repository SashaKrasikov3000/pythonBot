import telebot
import pymysql
import secrets
import requests
# TODO: придумать бота, добавить в репозиторий и отправить ссылку

bot = telebot.TeleBot("6922904535:AAE3PQK1lti5WWlz_2esy1oZfC_WWO9eFK4")
searching = False

@bot.message_handler(commands=["start"])
def greet_human(msg):
    bot.send_message(msg.chat.id, "Hello, I am here to help you with searching parts")


@bot.message_handler(commands=["find"])
def enable_searching(msg):
    global searching
    searching = True
    bot.send_message(msg.chat.id, "Searching mode enabled")


@bot.message_handler(commands=["stop"])
def stop_searching(msg):
    global searching
    searching = False
    bot.send_message(msg.chat.id, "Searching mode stopped")


@bot.message_handler(content_types=["text"])
def handle_text(msg):
    if searching:
        if msg.text.isnumeric():
            result = search(msg)
            if result == -1:
                bot.send_message(msg.chat.id, "Connection refused")
            else:
                bot.send_message(msg.chat.id, result)   # Create and send result
        else:
            bot.send_message(msg.chat.id, "Part number must be int")
    else:
        bot.send_message(msg.chat.id, "Use commands")


def search(msg):
    try:
        conn = pymysql.connect(
            host=secrets.host,
            port=secrets.port,
            user=secrets.user,
            password=secrets.password,
            database=secrets.database
        )
        print("Connected")
        cursor = conn.cursor()
        cursor.execute(f"SELECT name, price, amount_warehouse1 from shop_products WHERE article = {msg.text}")   # 3948095
        out = cursor.fetchall()
        conn.close()
        for row in out:
            print(row)
        return 0

    except Exception as ex:
        print("Connection refused: ", ex)
        return -1

bot.infinity_polling()
