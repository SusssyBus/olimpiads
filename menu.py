import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import datetime
import sqlite3
from dotenv import load_dotenv
import os
con = sqlite3.connect("TEST_db.db")
load_dotenv()
bot_token = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(bot_token)

@bot.message_handler(commands=["start"])
def hello(message):
    start_text = "Здравствуйте, этот бот поможет вам не забыть про свои олимпиады! Он будет напоминать вам про начало именно ваших олимпиад.\n\nПо кнопке ниже вы можете перейти в меню для настройки напоминаний. Также в меню можно попасть по команде \"\\menu\""
    keyboard = InlineKeyboardMarkup()
    #в будущем добавляем сюда ссылку сайт
    menu_button = InlineKeyboardButton("Главное меню", callback_data="go_to_menu")
    keyboard.add(menu_button)
    bot.send_message(message.chat.id, text=start_text, reply_markup=keyboard)
@bot.message_handler(commands=["menu"])
def menu_command(message):
    menu(message.chat.id)
@bot.callback_query_handler(func=lambda call: call.data=="go_to_menu")
def menu_call(call):
    menu(call.message.chat.id)
def menu(id):
    menu_text = "Здесь вы можете найти интересующую вас олимпиаду, либо управлять сделанными вами подписками(в разработке)."
    keyboard = InlineKeyboardMarkup()
    subscribe = InlineKeyboardButton("Мои подписки", callback_data="dodelaite_bazu_dannih")
    olimpiad = InlineKeyboardButton("Найти олимпиаду", callback_data="brand:")
    keyboard.add(olimpiad, subscribe)
    bot.send_message(id, text=menu_text, reply_markup=keyboard)
@bot.callback_query_handler(func=lambda call: call.data[5] == ":")
def search_management(call):
    skip_turn = False
    if call.data[:5] == "brand":
        con = sqlite3.connect("TEST_db.db")
        cursor = con.cursor()
        keyboard = InlineKeyboardMarkup()
        read_brand = "SELECT brand_id, brand_name FROM brand"
        cursor.execute(read_brand)
        data = cursor.fetchall()
        for i in data:
            button = InlineKeyboardButton(i[1], callback_data=(f"sbjct:{i[0]}"))
            keyboard.add(button)
        button = InlineKeyboardButton("Назад в главное меню", callback_data="go_to_menu")
        keyboard.add(button)
        bot.send_message(call.message.chat.id, "Выберите олимпиаду:", reply_markup=keyboard)
        cursor.close()
        con.close()
    elif call.data[:5] == "sbjct":
        con = sqlite3.connect("TEST_db.db")
        cursor = con.cursor()
        keyboard = InlineKeyboardMarkup()
        read_subject = f"SELECT subject_id, subject_name FROM subject WHERE brand_id = {call.data[6:]}"
        cursor.execute(read_subject)
        data = cursor.fetchall()
        for i in data:
            button = InlineKeyboardButton(i[1], callback_data=f"stage:{i[0]}")
            keyboard.add(button)
        button = InlineKeyboardButton("Назад в главное меню", callback_data="go_to_menu")
        keyboard.add(button)
        bot.send_message(call.message.chat.id, "Выберите предмет участия:", reply_markup=keyboard)
        cursor.close()
        con.close()
    elif call.data[:5] == "stage":
        con = sqlite3.connect("TEST_db.db")
        cursor = con.cursor()
        keyboard = InlineKeyboardMarkup()
        date = int(datetime.datetime.now().year)
        next = str(date) + "/" + str(date + 1)
        prev = str(date - 1) + "/" + str(date)
        read_stage = f"SELECT stage_id, stage_name FROM stage, season WHERE subject_id = {call.data[6:]} AND stage.season_id = season.season_id AND (season_name = \"{next}\" OR season_name = \"{prev}\")"
        cursor.execute(read_stage)
        data = cursor.fetchall()
        for i in data:
            button = InlineKeyboardButton(i[1], callback_data=f"turns:{i[0]}")
            keyboard.add(button)
        button = InlineKeyboardButton("Назад в главное меню", callback_data="go_to_menu")
        keyboard.add(button)
        bot.send_message(call.message.chat.id, "Выберите этап олимпиады:", reply_markup=keyboard)
        cursor.close()
        con.close()
    elif call.data[:5] == "turns":
        con = sqlite3.connect("TEST_db.db")
        cursor = con.cursor()
        keyboard = InlineKeyboardMarkup()
        read_turn = f"SELECT turn_id, turn_name FROM turn WHERE stage_id = {call.data[6:]}"
        cursor.execute(read_turn)
        data = cursor.fetchall()
        for i in data:
            button = InlineKeyboardButton(i[1], callback_data=f"class:{i[0]}")
            keyboard.add(button)
        button = InlineKeyboardButton("Назад в главное меню", callback_data="go_to_menu")
        keyboard.add(button)
        skip_turn = (len(data) <= 1)
        if not skip_turn:
            bot.send_message(call.message.chat.id, "Выберите номер тура олимпиады:", reply_markup=keyboard)
        else:
            turn_id = f"class:{data[0][0]}"
        cursor.close()
        con.close()
    if skip_turn or call.data[:5] == "class":
        if not skip_turn:
            turn_id = call.data
        con = sqlite3.connect("TEST_db.db")
        cursor = con.cursor()
        keyboard = InlineKeyboardMarkup()
        read_class = f"SELECT class_id, class_name FROM class WHERE turn_id = {turn_id[6:]}"
        cursor.execute(read_class)
        data = cursor.fetchall()
        for i in data:
            button = InlineKeyboardButton(i[1], callback_data=f"ThEnd:")
            keyboard.add(button)
        button = InlineKeyboardButton("Назад в главное меню", callback_data="go_to_menu")
        keyboard.add(button)
        bot.send_message(call.message.chat.id, "Выберите класс участия:", reply_markup=keyboard)
        cursor.close()
        con.close()
    if call.data[:5] == "ThEnd":
        end_text = "К сожалению, разработчики не добавили ничего про эту олимпиаду, можете вернуться в главное меню"
        keyboard = InlineKeyboardMarkup()
        button = InlineKeyboardButton("Назад в глваное меню", callback_data="go_to_menu")
        keyboard.add(button)
        bot.send_message(call.message.chat.id, text="К сожалению, разработчики не добавили ничего про эту олимпиаду, можете вернуться в главное меню", reply_markup=keyboard)

bot.infinity_polling()