import telebot
import requests

bot = telebot.TeleBot("TOKEN")

@bot.message_handler(commands=["start"])
def greet_human(message):
    bot.send_message(message.chat.id, "Hello")
# TODO: придумать бота, добавить в репозиторий и отправить ссылку
# @bot.message_handler(commands=["weather"])
# def send_weather(message):
#     weather = requests.get(f"https://api.openweathermap.org/data/2.5/weather?lat={40}&lon={40}&appid=a86c840216813bf0510e2919d86f24b2")