from telegram.ext import Updater, Filters, CommandHandler, ConversationHandler, MessageHandler, RegexHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from urllib.parse import unquote
import json
import os
from QIWI_API import UserQiwi
from QIWI_API import QiwiError, TokenError, TransactionNotFound, WalletError, MapError, NotFoundAddress, CheckError, \
    WrongEmail, WrongNumber, TransactionError

VERSION = "Bot v1.0\nQiwiAPI v1.0"
LANGUAGE = "eng"
LANGUAGES = json.load(open("Languages.json"))
DIALOGS = LANGUAGES[LANGUAGE]


def start(bot, update):
    update.message.reply_text(DIALOGS["start"])
    return 1


def check_token(bot, update, user_data):
    user_data["token"] = update.message.text
    try:
        user_data["user"] = UserQiwi(user_data["token"])
        markup = ReplyKeyboardMarkup(start_keyboard, one_time_keyboard=False)
        update.message.reply_text(DIALOGS["command"], reply_markup=markup)
        return 2
    except TokenError:
        update.message.reply_text(DIALOGS["error"])
        start(bot, update)


def balance(bot, update, user_data):
    try:
        update.message.reply_text(user_data["user"].get_balance())
        return 2
    except QiwiError:
        update.message.reply_text(DIALOGS["q_error"])
        return 2


def transactions(bot, update):
    markup = ReplyKeyboardMarkup(transactions_keyboard, one_time_keyboard=True)
    update.message.reply_text(DIALOGS["command"], reply_markup=markup)
    return 3


def check_status(bot, update):
    update.message.reply_text(DIALOGS["transaction_id"])
    return 4


def answer_about_transaction(bot, update, user_data):
    markup = ReplyKeyboardMarkup(start_keyboard, one_time_keyboard=False)
    try:
        update.message.reply_text(user_data["user"].get_info_about_transaction(update.message.text),
                                  reply_markup=markup)

    except TransactionNotFound:
        update.message.reply_text(DIALOGS["tr_error"], reply_markup=markup)
    return 2


def last(bot, update, user_data):
    markup = ReplyKeyboardMarkup(start_keyboard, one_time_keyboard=False)
    try:
        answer = user_data["user"].get_last_transactions()
        if not answer:
            update.message.reply_text(DIALOGS["no_recent_tr"], reply_markup=markup)
        else:
            update.message.reply_text(answer, reply_markup=markup)
    except TransactionNotFound:
        update.message.reply_text(DIALOGS["q_error"], reply_markup=markup)
    return 2


def terminals(bot, update, user_data):
    user_data["location_coords"] = False
    markup = ReplyKeyboardMarkup(terminals_keyboard, one_time_keyboard=True)
    update.message.reply_text(DIALOGS["command"], reply_markup=markup)
    return 5


def take_command_found_address(bot, update, user_data):
    user_data["map"] = update.message.text == DIALOGS["on map"]
    markup = ReplyKeyboardMarkup(terminals2_keyboard, one_time_keyboard=True)
    update.message.reply_text(DIALOGS["command"], reply_markup=markup)
    return 6


def take_address(bot, update):
    update.message.reply_text(DIALOGS["ent_address"])
    return 7


def take_locaion(bot, update, user_data):
    location = update.message.location
    coords = (location["longitude"], location["latitude"])

    user_data["location_coords"] = ",".join(map(str, coords))
    answer_about_terminates(bot, update, user_data)
    return 2


def answer_about_terminates(bot, update, user_data):
    markup = ReplyKeyboardMarkup(start_keyboard, one_time_keyboard=False)

    if update.message.text != DIALOGS["last ip"]:
        if user_data["location_coords"]:
            address = user_data["location_coords"]
        else:
            address = update.message.text
    else:
        address = None

    try:
        url, address = user_data["user"].get_map_terminates(address)
    except NotFoundAddress:
        update.message.reply_text(DIALOGS["wrong_address"], reply_markup=markup)
        return 2
    except MapError:
        update.message.reply_text(DIALOGS["data_error"], reply_markup=markup)
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
    markup = ReplyKeyboardMarkup(options_keyboard, one_time_keyboard=True)
    update.message.reply_text(DIALOGS["command"], reply_markup=markup)
    return 8


def get_info(bot, update, user_data):
    markup = ReplyKeyboardMarkup(start_keyboard, one_time_keyboard=False)
    update.message.reply_text(user_data["user"].get_info(), reply_markup=markup)
    return 2


def take_new_token(bot, update):
    update.message.reply_text(DIALOGS["new_token"])
    return 1


def update_user(bot, update, user_data):
    user_data["user"].update_info()
    markup = ReplyKeyboardMarkup(start_keyboard, one_time_keyboard=False)
    update.message.reply_text(DIALOGS["up_acc_inf"], reply_markup=markup)
    return 2


def version(bot, update):
    markup = ReplyKeyboardMarkup(start_keyboard, one_time_keyboard=False)
    update.message.reply_text(VERSION, reply_markup=markup)
    return 2


def check(bot, update, user_data):
    user_data["check_type_rest"] = None
    markup = ReplyKeyboardMarkup(check_keyboard, one_time_keyboard=True)
    update.message.reply_text(DIALOGS["command"], reply_markup=markup)
    return 9


def dialog_email(bot, update, user_data):
    user_data["check_type_rest"] = "email"
    user_data["email"] = None
    markup = ReplyKeyboardMarkup(email_keyboard, one_time_keyboard=True)
    update.message.reply_text(DIALOGS["command"], reply_markup=markup)
    return 10


def enter_email(bot, update):
    update.message.reply_text(DIALOGS["enter email"])
    return 11


def get_email(bot, update, user_data):
    user_data["email"] = update.message.text
    update.message.reply_text(DIALOGS["enter transaction id"])
    return 13


def enter_transaction_id(bot, update):
    update.message.reply_text(DIALOGS["enter transaction id"])
    return 13


def get_transaction_id(bot, update, user_data):
    markup = ReplyKeyboardMarkup(start_keyboard, one_time_keyboard=False)
    if user_data["check_type_rest"] == "email":
        if user_data["email"] is None:
            try:
                user_data["user"].send_check_email(update.message.text)
                update.message.reply_text(DIALOGS["sent check"], reply_markup=markup)
            except TransactionNotFound:
                update.message.reply_text(DIALOGS["tr_error"], reply_markup=markup)
            except WrongEmail:
                update.message.reply_text(DIALOGS["error email"], reply_markup=markup)
        else:
            try:
                user_data["user"].send_check_email(update.message.text, user_data["email"])
                update.message.reply_text(DIALOGS["sent check"], reply_markup=markup)
            except TransactionNotFound:
                update.message.reply_text(DIALOGS["tr_error"], reply_markup=markup)
            except WrongEmail:
                update.message.reply_text(DIALOGS["error email"], reply_markup=markup)

    else:
        name = str(update.message.chat_id) + ".jpeg"
        try:
            user_data["user"].get_image_check(update.message.text, name)
            bot.sendPhoto(update.message.chat_id, open(name, mode="rb"), reply_markup=markup)
        except TransactionNotFound:
            update.message.reply_text(DIALOGS["tr_error"], reply_markup=markup)
        except CheckError:
            update.message.reply_text(DIALOGS["check error"], reply_markup=markup)
        os.remove(name)
    return 2


def pay(bot, update, user_data):
    user_data["check_type_rest"] = None
    markup = ReplyKeyboardMarkup(pay_keyboard, one_time_keyboard=True)
    update.message.reply_text(DIALOGS["command"], reply_markup=markup)
    return 14


def enter_user_id(bot, update):
    update.message.reply_text(DIALOGS["enter user id"])
    return 17


def get_user_id(bot, update, user_data):
    user_data["user_id"] = update.message.text
    update.message.reply_text(DIALOGS["enter amount"])
    return 19


def mobile_phone(bot, update, user_data):
    user_data["check_type_rest"] = "mobile"
    user_data["number"] = None
    markup = ReplyKeyboardMarkup(mobile_keyboard, one_time_keyboard=True)
    update.message.reply_text(DIALOGS["command"], reply_markup=markup)
    return 15


def enter_mobile(bot, update):
    update.message.reply_text(DIALOGS["enter phone"])
    return 16


def get_mobile(bot, update, user_data):
    user_data["number"] = update.message.text
    update.message.reply_text(DIALOGS["enter amount"])
    return 19


def enter_amount(bot, update):
    update.message.reply_text(DIALOGS["enter amount"])
    return 19


def get_amount(bot, update, user_data):
    markup = ReplyKeyboardMarkup(start_keyboard, one_time_keyboard=False)
    if user_data["check_type_rest"] == "mobile":
        if user_data["number"] is None:
            try:
                update.message.reply_text(user_data["user"].transaction_telephone(update.message.text),
                                          reply_markup=markup)
            except TransactionNotFound:
                update.message.reply_text(DIALOGS["tr_s_error"], reply_markup=markup)
            except WrongNumber:
                update.message.reply_text(DIALOGS["error number"], reply_markup=markup)
            except WalletError:
                update.message.reply_text(DIALOGS["error wallet"], reply_markup=markup)
        else:
            try:
                update.message.reply_text(user_data["user"].transaction_telephone(update.message.text,
                                                                                  user_data["number"]),
                                          reply_markup=markup)
            except TransactionError:
                update.message.reply_text(DIALOGS["tr_s_error"], reply_markup=markup)
            except WrongNumber:
                update.message.reply_text(DIALOGS["error number"], reply_markup=markup)
            except WalletError:
                update.message.reply_text(DIALOGS["error wallet"], reply_markup=markup)
    else:
        try:
            update.message.reply_text(user_data["user"].transaction_qiwi(user_data["user_id"], update.message.text),
                                      reply_markup=markup)
        except TransactionError:
            update.message.reply_text(DIALOGS["tr_s_error"], reply_markup=markup)
        except WalletError:
            update.message.reply_text(DIALOGS["error wallet"], reply_markup=markup)
    return 2


def wrong_answer(bot, update):
    update.message.reply_text(DIALOGS["wrong_answer"])


def back(bot, update):
    markup = ReplyKeyboardMarkup(start_keyboard, one_time_keyboard=False)
    update.message.reply_text(DIALOGS["command"], reply_markup=markup)
    return 2


def stop(bot, update):
    update.message.reply_text(DIALOGS["off"], reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


button_back = ["/{}".format(DIALOGS["back"])]

start_keyboard = [["/{}".format(DIALOGS["balance"]), "/{}".format(DIALOGS["pay"])],
                  ["/{}".format(DIALOGS["transactions"]), "/{}".format(DIALOGS["check"])],
                  ["/{}".format(DIALOGS["terminals"]), "/{}".format(DIALOGS["options"])]]

transactions_keyboard = [[DIALOGS["check status"], DIALOGS["last"]],
                         button_back]

terminals_keyboard = [[DIALOGS["on map"], DIALOGS["address"]],
                      button_back]
terminals2_keyboard = [[DIALOGS["last ip"], DIALOGS["enter address"]],
                       button_back]

options_keyboard = [[DIALOGS["change token"], DIALOGS["version"]],
                    [DIALOGS["update user"], DIALOGS["get info"]],
                    button_back]

check_keyboard = [[DIALOGS["get image"], DIALOGS["send to email"]],
                  button_back]
email_keyboard = [[DIALOGS["my email"], DIALOGS["other email"]],
                  button_back]

pay_keyboard = [[DIALOGS["mobile phone"], DIALOGS["qiwi user"]],
                button_back]
mobile_keyboard = [[DIALOGS["my phone"], DIALOGS["other phone"]],
                   button_back]

markup = None


def main():
    updater = Updater("TOKEN")
    dp = updater.dispatcher
    command_back = CommandHandler(LANGUAGES[LANGUAGE]["back"], back)
    wrong_answer_hd = MessageHandler(Filters.text, wrong_answer)

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={1: [MessageHandler(Filters.text, check_token, pass_user_data=True)],
                2: [CommandHandler(DIALOGS["balance"], balance, pass_user_data=True),
                    CommandHandler(DIALOGS["pay"], pay, pass_user_data=True),
                    CommandHandler(DIALOGS["transactions"], transactions),
                    CommandHandler(DIALOGS["check"], check, pass_user_data=True),
                    CommandHandler(DIALOGS["terminals"], terminals, pass_user_data=True),
                    CommandHandler(DIALOGS["options"], options),
                    wrong_answer_hd],

                3: [RegexHandler("^{}$".format(DIALOGS["check status"]), check_status),
                    RegexHandler("^{}$".format(DIALOGS["last"]), last, pass_user_data=True),
                    command_back, wrong_answer_hd],
                4: [MessageHandler(Filters.text, answer_about_transaction, pass_user_data=True)],

                5: [RegexHandler("{}|{}".format(DIALOGS["on map"], DIALOGS["address"]),
                                 take_command_found_address, pass_user_data=True),
                    command_back, wrong_answer_hd],
                6: [RegexHandler("^{}$".format(DIALOGS["enter address"]), take_address),
                    RegexHandler("^{}$".format(DIALOGS["last ip"]), answer_about_terminates,
                                 pass_user_data=True),
                    command_back, wrong_answer_hd],
                7: [MessageHandler(Filters.text, answer_about_terminates, pass_user_data=True),
                    MessageHandler(Filters.location, take_locaion, pass_user_data=True)],

                8: [RegexHandler("^{}$".format(DIALOGS["change token"]), take_new_token),
                    RegexHandler("^{}$".format(DIALOGS["update user"]), update_user, pass_user_data=True),
                    RegexHandler("^{}$".format(DIALOGS["version"]), version),
                    RegexHandler("^{}$".format(DIALOGS["get info"]), get_info, pass_user_data=True),
                    command_back, wrong_answer_hd],

                9: [RegexHandler("^{}$".format(DIALOGS["get image"]), enter_transaction_id),
                    RegexHandler("^{}$".format(DIALOGS["send to email"]), dialog_email, pass_user_data=True),
                    command_back, wrong_answer_hd],

                10: [RegexHandler("^{}$".format(DIALOGS["my email"]), enter_transaction_id),
                     RegexHandler("^{}$".format(DIALOGS["other email"]), enter_email),
                     command_back, wrong_answer_hd],

                11: [MessageHandler(Filters.text, get_email, pass_user_data=True)],
                12: [MessageHandler(Filters.text, enter_transaction_id)],
                13: [MessageHandler(Filters.text, get_transaction_id, pass_user_data=True)],

                14: [RegexHandler("^{}$".format(DIALOGS["qiwi user"]), enter_user_id),
                     RegexHandler("^{}$".format(DIALOGS["mobile phone"]), mobile_phone, pass_user_data=True),
                     command_back, wrong_answer_hd],

                15: [RegexHandler("^{}$".format(DIALOGS["my phone"]), enter_amount),
                     RegexHandler("^{}$".format(DIALOGS["other phone"]), enter_mobile),
                     command_back, wrong_answer_hd],

                16: [MessageHandler(Filters.text, get_mobile, pass_user_data=True)],
                17: [MessageHandler(Filters.text, get_user_id, pass_user_data=True)],
                18: [MessageHandler(Filters.text, enter_amount)],
                19: [MessageHandler(Filters.text, get_amount, pass_user_data=True)]},

        fallbacks=[CommandHandler("stop", stop)]
    )

    dp.add_handler(conv_handler)

    print("Bot started...")

    updater.start_polling()

    updater.idle()


if __name__ == "__main__":
    main()
