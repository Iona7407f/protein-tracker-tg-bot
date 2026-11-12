import telebot
from telebot import types
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')

bot = telebot.TeleBot(token='8407611486:AAH5LQNf7HCQRspUBN85uaPT9OBWGXj9cs8')
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    button1 = types.KeyboardButton("Моя суточная норма")
    button2 = types.KeyboardButton("Подсчет белка за день")
    markup.add(button1, button2)
    bot.send_message(message.chat.id,
    'Это бот для подсчета белочка, нажимай кнопки в менюшке чтобы попробовать его функции', reply_markup=markup)

@bot.message_handler(commands=['stop'])
def stop(message):
    bot.send_message(message.chat.id, 'Бот остановлен. Напишите /start для возобновления')

user_weights = {}
users_daily_norm = {}
current_food = {}
product_dict = {
    'Мясо': {
        'Курица': 25,
        'Говядина': 23,
        'Свинина': 22
    },
    'Молочка': {
        'Творог': 16,
        'Сыр': 27,
        'Греческий йогурт': 9
    }
}

@bot.message_handler(content_types=['text'])
def daily_norm(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if message.text == 'Моя суточная норма':
        bot.send_message(message.chat.id, 'Введи свой вес')
        bot.register_next_step_handler(message, save_weights)
    elif message.text == 'Подсчет белка за день':
        buttons = []
        for product in product_dict:
            buttons.append(types.KeyboardButton(product))
        markup.add(*buttons)
        markup.add(types.KeyboardButton('Назад'))
        bot.send_message(message.chat.id, 'Что ел(а)? Выбирай из списка', reply_markup=markup)
        bot.register_next_step_handler(message, count_proteine)
def save_weights(message):
    user_id = message.chat.id
    user_weights[user_id] = message.text

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Умеренный")
    btn2 = types.KeyboardButton("Активный")
    btn3 = types.KeyboardButton("Интенсивный")
    btn4 = types.KeyboardButton("Назад")
    markup.add(btn1, btn2, btn3, btn4)
    bot.send_message(message.chat.id, 'Какой у тебя образ жизни?', reply_markup=markup)
    bot.register_next_step_handler(message, users_lifestyle)

coef_dict = {
    'Умеренный':'1.3',
    'Активный':'1.5',
    'Интенсивный':'1.8'
}

def users_lifestyle(message):
    if message.text == 'Назад':
        start(message)
        return
    weight = user_weights[message.chat.id]
    coef = coef_dict[message.text]
    result = float(coef) * int(weight)
    bot.send_message(message.chat.id, f"Твоя суточная норма белка {result} грамм" )
    start(message)

def count_proteine(message):
    category = message.text
    user_id = message.chat.id

    if category == 'Назад':
       start(message)
       return
    if category == 'Рассчитать':
       total = round(users_daily_norm.get(user_id, 0), 1)
       bot.send_message(message.chat.id, f"Итого: {total} грамм")
       start(message)
       return
    if category in product_dict:
       buttons = []
       markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
       products = product_dict[category]
       for item in products:
        buttons.append(types.KeyboardButton(item))
       markup.add(types.KeyboardButton('Назад'))
       markup.add(*buttons)
       bot.send_message(message.chat.id, "Что именно?", reply_markup=markup)
       bot.register_next_step_handler(message, save_product_choice)

def save_product_choice(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if message.text == 'Назад':
        start(message)
        return
    user_id = message.chat.id
    current_food[user_id] = message.text
    bot.send_message(message.chat.id, "Сколько грамм?", reply_markup=markup)
    markup.add(types.KeyboardButton('Назад'))
    bot.register_next_step_handler(message, dosage)

def dosage(message):
    if message.text == 'Назад':
        start(message)
        return
    amount_in_grams = int(message.text)
    user_id = message.chat.id
    food_name = current_food[user_id]
    protein_per_100 = 0

    for category in product_dict:
        if food_name in product_dict[category]:
            protein_per_100 = product_dict[category][food_name]

    added_protein = (protein_per_100 / 100) * amount_in_grams

    if user_id not in users_daily_norm:
        users_daily_norm[user_id] = 0
    users_daily_norm[user_id] += added_protein
    bot.send_message(message.chat.id, f"Записано: {round(added_protein, 1)} грамм белка")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = []
    for product in product_dict:
        buttons.append(types.KeyboardButton(product))
    markup.add(*buttons)
    markup.add(types.KeyboardButton('Рассчитать'), types.KeyboardButton('Назад'))
    bot.send_message(message.chat.id, "Чето еще?Выбирай категорию или жми рассчитать", reply_markup=markup)
    bot.register_next_step_handler(message, count_proteine)

bot.infinity_polling()
