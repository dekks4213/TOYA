import csv
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from io import StringIO

# Используем ваш токен бота
bot = telebot.TeleBot("6742813805:AAGhaheSKRimtFrKJJpM_dizzOb2OrQX8pQ")

# Ссылка для скачивания CSV-файла с Google Sheets
csv_url = "https://docs.google.com/spreadsheets/d/1n1GGx5AKQQA5JxpeuAvbbSrDRvk1gvffwJfh6XoKsko/export?format=csv"


def download_csv():
    response = requests.get(csv_url)
    response.encoding = 'utf-8'
    return StringIO(response.text)


def find_column_name(columns, keyword):
    """Функция для поиска названия колонки по ключевому слову"""
    for column in columns:
        if keyword in column:
            return column
    raise KeyError(f"Колонка с ключевым словом '{keyword}' не найдена")


def parse_csv():
    csv_data = download_csv()

    # Пропускаем первые 13 строк, чтобы начать с заголовков
    for _ in range(13):
        next(csv_data)

    reader = csv.DictReader(csv_data)
    columns = reader.fieldnames  # Список всех заголовков

    try:
        # Ищем названия колонок по ключевым словам
        purchase_date_col = find_column_name(columns, 'Дата')
        status_col = find_column_name(columns, 'Статус')
        model_col = find_column_name(columns, 'Модель')
        chassis_number_col = find_column_name(columns, 'Номер')
        year_col = find_column_name(columns, 'Год')
        specification_col = find_column_name(columns, 'Спецификация')
        media_col = find_column_name(columns, 'Фото')
        configuration_col = find_column_name(columns, 'Комплектация')
        auction_link_col = find_column_name(columns, 'Ссылка')
        final_cost_col = find_column_name(columns, 'Итог')

    except KeyError as e:
        print(f"Ошибка: {e}")
        return ["Ошибка в заголовках колонок. Проверьте правильность заголовков в CSV файле."]

    car_list = []

    for row in reader:
        # Пропускаем строки, если поле "Модель" пустое
        if not row[model_col]:
            continue

        # Получаем значения для каждой колонки
        purchase_date = row[purchase_date_col]
        status = row[status_col]
        model = row[model_col]
        chassis_number = row[chassis_number_col]  # Передаем полный номер кузова
        year = row[year_col]
        specification = row[specification_col]
        media = row[media_col]
        configuration = row[configuration_col]
        auction_link = row[auction_link_col]
        final_cost = row[final_cost_col]

        # Форматирование ссылки на медиа
        media_text = f"[Посмотреть фото/видео]({media})" if media else "Нет фото/видео"
        auction_text = f"[Ссылка на аукцион]({auction_link})" if auction_link else "Нет ссылки на аукцион"

        # Форматирование сообщения
        car_info = (
            f"🚗 **Модель**: {model}\n"
            f"📅 **Дата покупки**: {purchase_date}\n"
            f"📄 **Статус**: {status}\n\n"
            f"🔢 **Номер кузова**: {chassis_number}\n"
            f"📆 **Год выпуска**: {year}\n"
            f"⚙️ **Спецификация**: {specification}\n"
            f"🛠️ **Комплектация**: {configuration}\n\n"
            f"🎥 {media_text}\n"
            f"🌐 {auction_text}\n\n"
            f"💰 **Итог в РФ**: {final_cost} руб.\n"
            "━━━━━━━━━━━━━━━━━\n"
        )
        car_list.append(car_info)

    return car_list


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message,
                 "Привет! Этот бот помогает получать информацию о машинах. Используйте команду /get_cars для получения списка.")


@bot.message_handler(commands=['get_cars'])
def send_car_list(message):
    car_list = parse_csv()
    for car_info in car_list[:-1]:  # Отправляем все сообщения, кроме последнего
        bot.send_message(message.chat.id, car_info, parse_mode="Markdown")

    # Создаем клавиатуру с кнопкой для последнего сообщения
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Запросить актуальный список", callback_data="get_cars"))

    # Отправляем последнее сообщение с кнопкой
    bot.send_message(message.chat.id, car_list[-1], parse_mode="Markdown", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "get_cars")
def callback_get_cars(call):
    # Удаляем сообщение с кнопкой, чтобы не было повторного нажатия
    bot.delete_message(call.message.chat.id, call.message.message_id)
    # Отправляем актуальный список снова
    send_car_list(call.message)


# Запуск бота
bot.polling()