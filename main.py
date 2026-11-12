import telebot
from telebot import types
from dotenv import load_dotenv
import json
import os
from threading import RLock

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bot_data.json')
data_lock = RLock()

def load_data():
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


saved_data = load_data()
user_weights = {
    int(key): value for key, value in saved_data.get('user_weights', {}).items()
}
daily_protein = {
    int(key): value for key, value in saved_data.get('daily_protein', {}).items()
}
current_food = {
    int(key): value for key, value in saved_data.get('current_food', {}).items()
}


def save_data():
    with data_lock:
        data = {
            'user_weights': user_weights,
            'daily_protein': daily_protein,
            'current_food': current_food
        }
        temporary_file = DATA_FILE + '.tmp'
        with open(temporary_file, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        os.replace(temporary_file, DATA_FILE)


product_dict = {
    'Мясо': {
        'Курица': 25,
        'Говядина': 23,
        'Свинина': 22
    },
    'Молочка': {
        'Творог': 16,
        'Сыр': 27,
        'Йогурт': 9
    }
}

coef_dict = {
    'Умеренный': 1.3,
    'Активный': 1.5,
    'Интенсивный': 1.8
}

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = types.KeyboardButton("Моя суточная норма")
    button2 = types.KeyboardButton("Подсчет белка за день")
    markup.add(button1, button2)
    bot.send_message(
        message.chat.id,
        'Это бот для подсчета белка, нажимай кнопки в менюшке '
        'чтобы попробовать его функции',
        reply_markup=markup
    )

@bot.message_handler(commands=['stop'])
def stop(message):
    bot.send_message(
        message.chat.id,
        'Бот остановлен. Напишите /start для возобновления'
    )

@bot.message_handler(content_types=['text'])
def daily_norm(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    if message.text == 'Моя суточная норма':
        bot.send_message(message.chat.id, 'Введи свой вес')
        bot.register_next_step_handler(message, save_weights)

    elif message.text == 'Подсчет белка за день':
        with data_lock:
            daily_protein[message.chat.id] = 0
            save_data()
        buttons = [
            types.KeyboardButton(product) for product in product_dict
        ]
        markup.add(*buttons)
        markup.add(types.KeyboardButton('Назад'))
        bot.send_message(
            message.chat.id,
            'Что ел(а)? Выбирай из списка',
            reply_markup=markup
        )
        bot.register_next_step_handler(message, count_proteine)

def save_weights(message):
    if message.text == 'Назад':
        start(message)
        return

    try:
        weight = int(message.text)
        if weight <= 0:
            raise ValueError
    except (ValueError, TypeError):
        bot.send_message(message.chat.id, 'Введи вес целым положительным числом')
        bot.register_next_step_handler(message, save_weights)
        return

    with data_lock:
        user_weights[message.chat.id] = weight
        save_data()

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        types.KeyboardButton("Умеренный"),
        types.KeyboardButton("Активный"),
        types.KeyboardButton("Интенсивный"),
        types.KeyboardButton("Назад")
    )
    bot.send_message(
        message.chat.id,
        'Какой у тебя образ жизни?',
        reply_markup=markup
    )
    bot.register_next_step_handler(message, users_lifestyle)


def users_lifestyle(message):
    if message.text == 'Назад':
        start(message)
        return

    if message.text not in coef_dict:
        bot.send_message(message.chat.id, 'Выбери образ жизни кнопкой из меню')
        bot.register_next_step_handler(message, users_lifestyle)
        return

    weight = user_weights[message.chat.id]
    coef = coef_dict[message.text]
    result = round(coef * weight, 1)
    bot.send_message(
        message.chat.id,
        f"Твоя суточная норма белка {result} грамм"
    )
    start(message)


def count_proteine(message):
    category = message.text
    user_id = message.chat.id

    if category == 'Назад':
        start(message)
        return

    if category == 'Рассчитать':
        total = round(daily_protein.get(user_id, 0), 1)
        bot.send_message(message.chat.id, f"Итого: {total} грамм")
        start(message)
        return

    if category in product_dict:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        products = product_dict[category]
        buttons = [types.KeyboardButton(item) for item in products]
        markup.add(types.KeyboardButton('Назад'))
        markup.add(*buttons)
        bot.send_message(
            message.chat.id,
            "Что именно?",
            reply_markup=markup
        )
        bot.register_next_step_handler(message, save_product_choice, category)
        return

    bot.send_message(message.chat.id, 'Выбери категорию кнопкой из меню')
    bot.register_next_step_handler(message, count_proteine)


def save_product_choice(message, category):
    if message.text == 'Назад':
        start(message)
        return

    if message.text not in product_dict[category]:
        bot.send_message(message.chat.id, 'Выбери продукт кнопкой из меню')
        bot.register_next_step_handler(message, save_product_choice, category)
        return

    with data_lock:
        current_food[message.chat.id] = message.text
        save_data()

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('Назад'))
    bot.send_message(
        message.chat.id,
        "Сколько грамм?",
        reply_markup=markup
    )
    bot.register_next_step_handler(message, dosage)


def dosage(message):
    if message.text == 'Назад':
        start(message)
        return

    try:
        amount_in_grams = int(message.text)
        if amount_in_grams <= 0:
            raise ValueError
    except (ValueError, TypeError):
        bot.send_message(
            message.chat.id,
            'Введи количество грамм целым положительным числом'
        )
        bot.register_next_step_handler(message, dosage)
        return

    user_id = message.chat.id
    food_name = current_food[user_id]
    protein_per_100 = 0

    for products in product_dict.values():
        if food_name in products:
            protein_per_100 = products[food_name]
            break

    added_protein = (protein_per_100 / 100) * amount_in_grams

    with data_lock:
        daily_protein[user_id] = daily_protein.get(user_id, 0) + added_protein
        save_data()

    bot.send_message(
        message.chat.id,
        f"Записано: {round(added_protein, 1)} грамм белка"
    )

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = [
        types.KeyboardButton(product) for product in product_dict
    ]
    markup.add(*buttons)
    markup.add(
        types.KeyboardButton('Рассчитать'),
        types.KeyboardButton('Назад')
    )
    bot.send_message(
        message.chat.id,
        "Что-то еще? Выбирай категорию или жми рассчитать",
        reply_markup=markup
    )
    bot.register_next_step_handler(message, count_proteine)

bot.infinity_polling()