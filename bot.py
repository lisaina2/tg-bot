import telebot
import requests
import json
import os

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8265805893:AAHFosVRaq03Jout5e79zXTzXsVY7qC78LU")
bot = telebot.TeleBot(BOT_TOKEN)
FAVORITES_FILE = 'favorites.json'

# Функция для загрузки избранных вакансий из файла.  Возвращает список.
def load_favorites():
    try:
        with open(FAVORITES_FILE, 'r', encoding='utf-8') as f:
            favorites = json.load(f)
            if not isinstance(favorites, list):  # Проверка типа, если в файле не список
                return []
        return favorites
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        return []

# Функция для сохранения избранных вакансий в файл.
def save_favorites(favorites):
    with open(FAVORITES_FILE, 'w', encoding='utf-8') as f:
        json.dump(favorites, f, ensure_ascii=False, indent=4)

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Привет! Используй /search [запрос] для поиска.")

@bot.message_handler(commands=['search'])
def search(message):
    try:
        query = message.text.split(' ', 1)[1]  # Извлекаем запрос, если есть аргумент
    except IndexError:
        bot.send_message(message.chat.id, "Пожалуйста, укажите запрос после команды /search.")
        return  # Важно: выходим из функции, если нет аргумента

    url = f"https://api.hh.ru/vacancies?text={query}&per_page=5"
    response = requests.get(url)
    data = response.json()

    for item in data['items']:
        employer_name = item['employer']['name'] if 'employer' in item and 'name' in item['employer'] else "Не указан"
        salary = item.get('salary')
        salary_text = ""
        if salary:
            salary_from = salary.get('from')
            salary_to = salary.get('to')
            currency = salary.get('currency')
            if salary_from and salary_to:
                salary_text = f"{salary_from} - {salary_to} {currency}"
            elif salary_from:
                salary_text = f"от {salary_from} {currency}"
            elif salary_to:
                salary_text = f"до {salary_to} {currency}"
            else:
                salary_text = "Не указана"
        else:
            salary_text = "Не указана"


        text = f"Вакансия: {item['name']}\nЗарплата: {salary_text}\nРаботодатель: {employer_name}\nСсылка: {item['alternate_url']}"
        keyboard = telebot.types.InlineKeyboardMarkup()
        # Проверка, является ли элемент словарем и содержит ли ключ 'id'
        is_favorited = item['id'] in [fav['id'] if isinstance(fav, dict) and 'id' in fav else None for fav in load_favorites()]
        button_text = "Удалить из избранного" if is_favorited else "В избранное"
        callback_data = f"fav_{item['id']}" if not is_favorited else f"unfav_{item['id']}"

        show_more_button = telebot.types.InlineKeyboardButton(text="Показать еще", callback_data=f"show_more_{item['id']}")  # Добавлена кнопка "Показать еще"
        favorite_button = telebot.types.InlineKeyboardButton(text=button_text, callback_data=callback_data)

        keyboard.add(show_more_button,favorite_button) #Кнопка "Показать еще" слева кнопки избранного
        bot.send_message(message.chat.id, text, reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith('show_more_'))  # Обработчик кнопки "Показать еще"
def callback_inline(call):
    vacancy_id = call.data.split('_')[2]  # Получаем ID вакансии из callback_data
    #  Тут нужно реализовать логику получения full description  с hh.ru
    bot.send_message(call.message.chat.id, f"Описание для ID {vacancy_id} пока не реализовано.")

bot.infinity_polling()
