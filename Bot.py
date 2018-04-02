from telegram.ext import Updater, Filters, CommandHandler, ConversationHandler, MessageHandler, RegexHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from urllib.parse import unquote
from QIWI_API import UserQiwi
from QIWI_API import QiwiError, SintaksisError, TokenError, NoRightsError, TransactionNotFound, WalletError, \
    HistoryError, MapError, NotFoundAddress


VERSION = "Bot v0.1\nQiwiAPI v0.1"


def start(bot, update):
    update.message.reply_text("Please enter your token")
    return 1


def check_token(bot, update, user_data):
    user_data["token"] = update.message.text
    try:
        user_data["user"] = UserQiwi(user_data["token"])
        markup = ReplyKeyboardMarkup(start_keyboard, one_time_keyboard=False)
        update.message.reply_text("Select command", reply_markup=markup)
        return 2
    except TokenError:
        update.message.reply_text("Error!")
        start(bot, update)


def balance(bot, update, user_data):
    try:
        update.message.reply_text(user_data["user"].get_balance())
        return 2
    except QiwiError:
        update.message.reply_text("Failed to execute query")
        return 2


def transactions(bot, update):
    markup = ReplyKeyboardMarkup(transactions_keyboard, one_time_keyboard=False)
    update.message.reply_text("Select command", reply_markup=markup)
    return 3


def check_status(bot, update):
    update.message.reply_text("Enter transaction id")
    return 4


def answer_about_transaction(bot, update, user_data):
    markup = ReplyKeyboardMarkup(start_keyboard, one_time_keyboard=False)
    try:
        update.message.reply_text(user_data["user"].get_info_about_transaction(update.message.text),
                                  reply_markup=markup)

    except TransactionNotFound:
        update.message.reply_text("Error. Transaction not found", reply_markup=markup)
    return 2


def last(bot, update, user_data):
    markup = ReplyKeyboardMarkup(start_keyboard, one_time_keyboard=False)
    try:
        answer = user_data["user"].get_last_transactions()
        if not answer:
            update.message.reply_text("There are no recent transactions", reply_markup=markup)
        else:
            update.message.reply_text("There are no recent transactions", reply_markup=markup)
    except TransactionNotFound:
        update.message.reply_text("Query execution failed", reply_markup=markup)
    return 2


def terminals(bot, update):
    markup = ReplyKeyboardMarkup(terminals_keyboard, one_time_keyboard=False)
    update.message.reply_text("Select command", reply_markup=markup)
    return 5


def take_address(bot, update, user_data):
    user_data["map"] = update.message.text == "on map"
    update.message.reply_text("Enter address")
    return 6


def answer_about_terminates(bot, update, user_data):
    markup = ReplyKeyboardMarkup(start_keyboard, one_time_keyboard=False)
    try:
        url, address = user_data["user"].get_map_terminates(update.message.text)
    except NotFoundAddress:
        update.message.reply_text("Wrong address", reply_markup=markup)
        return 2
    except MapError:
        update.message.reply_text("Unable to retrieve data", reply_markup=markup)
        return 2

    if user_data["map"]:
        bot.sendPhoto(update.message.chat_id, url, reply_markup=markup)
    else:
        correct_address = []
        for i in address:
            try:
                word = unquote(unquote(i))
                if word:
                    correct_address.append(word)
            except TypeError:
                pass
        update.message.reply_text("\n".join(correct_address), reply_markup=markup)
    return 2


def options(bot, update):
    markup = ReplyKeyboardMarkup(options_keyboard, one_time_keyboard=False)
    update.message.reply_text("Select command", reply_markup=markup)
    return 7


def get_info(bot, update, user_data):
    markup = ReplyKeyboardMarkup(start_keyboard, one_time_keyboard=False)
    update.message.reply_text(user_data["user"].get_info(), reply_markup=markup)
    return 2


def take_new_token(bot, update):
    update.message.reply_text("Please enter your new token", reply_markup=markup)
    return 1


def update_user(bot, update, user_data):
    user_data["user"].update_info()
    markup = ReplyKeyboardMarkup(start_keyboard, one_time_keyboard=False)
    update.message.reply_text("Updated account information", reply_markup=markup)
    return 2


def version(bot, update):
    markup = ReplyKeyboardMarkup(start_keyboard, one_time_keyboard=False)
    update.message.reply_text(VERSION, reply_markup=markup)
    return 2


def not_found(bot, update):
    update.message.reply_text("Function will appear soon")
    return 2


def back(bot, update):
    markup = ReplyKeyboardMarkup(start_keyboard, one_time_keyboard=False)
    update.message.reply_text("Select command", reply_markup=markup)
    return 2


def stop(bot, update):
    update.message.reply_text("Shut down", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


start_keyboard = [["/balance", "/pay"], ["/transactions", "/check"], ["/terminals", "/options"]]
transactions_keyboard = [["check status", "last"], ["/back"]]
terminals_keyboard = [["on map", "address"], ["/back"]]
options_keyboard = [["change token", "version"], ["update user", "get info"], ["/back"]]
markup = None


def main():
    updater = Updater("TOKEN")
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={1: [MessageHandler(Filters.text, check_token, pass_user_data=True)],
                2: [CommandHandler("balance", balance, pass_user_data=True),
                    CommandHandler("pay", not_found),
                    CommandHandler("transactions", transactions),
                    CommandHandler("check", not_found),
                    CommandHandler("terminals", terminals),
                    CommandHandler("options", options)],

                3: [RegexHandler("^check status$", check_status),
                    RegexHandler("^last$", last, pass_user_data=True),
                    CommandHandler("back", back)],
                4: [MessageHandler(Filters.text, answer_about_transaction, pass_user_data=True)],

                5: [RegexHandler("on map|address", take_address, pass_user_data=True),
                    CommandHandler("back", back)],
                6: [MessageHandler(Filters.text, answer_about_terminates, pass_user_data=True)],

                7: [RegexHandler("^change token$", take_new_token),
                    RegexHandler("^update user$", update_user, pass_user_data=True),
                    RegexHandler("^version$", version),
                    RegexHandler("^get info$", get_info, pass_user_data=True),
                    CommandHandler("back", back)]},
        fallbacks=[CommandHandler("stop", stop)]
    )

    dp.add_handler(conv_handler)

    print("Bot started...")

    updater.start_polling()

    updater.idle()


if __name__ == "__main__":
    main()