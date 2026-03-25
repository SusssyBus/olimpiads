import telebot
import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
bot = telebot.TeleBot("8336413288:AAFSBveF_-4H9mtPRJj3SACQTMrjAQo9AlI")
import sqlite3
con = sqlite3.connect("TEST_db.db")

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
    menu_text = "бла бла бла бле бле бле блю блю блю"
    keyboard = InlineKeyboardMarkup()
    subscribe = InlineKeyboardButton("Мои подписки", callback_data="dodelaite_bazu_dannih")
    olimpiad = InlineKeyboardButton("Найти олимпиаду", callback_data="brands")
    keyboard.add(olimpiad, subscribe)
    bot.send_message(id, text=menu_text, reply_markup=keyboard)
@bot.callback_query_handler(func=lambda call: True)
def call_management(call):
    skip_turn = False
    if call.data == "brands":
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
        bot.send_message(call.message.chat.id, "Выберите бренд олимпиады:", reply_markup=keyboard)
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
        bot.send_message(call.message.chat.id, "Выберите предмет олимпиады:", reply_markup=keyboard)
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
            bot.send_message(call.message.chat.id, "Я так и не понял что это, но выбирайте:", reply_markup=keyboard)
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
            button = InlineKeyboardButton(i[1], callback_data=f"TheEnd")
            keyboard.add(button)
        button = InlineKeyboardButton("Назад в главное меню", callback_data="go_to_menu")
        keyboard.add(button)
        bot.send_message(call.message.chat.id, "Выберите класс участия:", reply_markup=keyboard)
        cursor.close()
        con.close()
    if call.data == "TheEnd":
        end_text = "К сожалению, разработчики не добавили ничего про эту олимпиаду, можете вернуться в главное меню"
        keyboard = InlineKeyboardMarkup()
        button = InlineKeyboardButton("Назад в глваное меню", callback_data="go_to_menu")
        keyboard.add(button)
        bot.send_message(call.message.chat.id, text="К сожалению, разработчики не добавили ничего про эту олимпиаду, можете вернуться в главное меню", reply_markup=keyboard)

bot.infinity_polling()