import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
bot = telebot.TeleBot("8336413288:AAFSBveF_-4H9mtPRJj3SACQTMrjAQo9AlI")
import sqlite3
con = sqlite3.connect("TEST_db.db")
cursor = con.cursor()

@bot.message_handler(commands=["start"])
def hello(message):
    start_text = "Здравствуйте, этот бот поможет вам не забыть про свои олимпиады! Он будет напоминать вам про начало именно ваших олимпиад.\n\nПо кнопке ниже вы можете перейти в меню для настройки напоминаний. Также в меню можно попасть по команде \"\\menu\""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    #в будущем добавляем сюда ссылку сайт
    menu_button = KeyboardButton("/menu")
    keyboard.add(menu_button)
    bot.send_message(message.chat.id, text=start_text, reply_markup=keyboard)
#^^^старт бота^^^
@bot.message_handler(commands=["menu"])
def menu(message):
    menu_text = "бла бла бла бле бле бле блю блю блю"
    keyboard = InlineKeyboardMarkup()
    subscribe = InlineKeyboardButton("Мои подписки", callback_data="subscribe")
    olimpiad = InlineKeyboardButton("Найти олимпиаду", callback_data="brand")
    keyboard.add(olimpiad, subscribe)
    bot.send_message(message.chat.id, text=menu_text, reply_markup=keyboard)

bot.infinity_polling()