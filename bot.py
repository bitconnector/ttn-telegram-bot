#!/bin/python

from ttnWatchdog import Watchdog
from liveLocation import LiveLocation
import time
import ttn

import json
import configparser

import telegram
from telegram.ext import Updater, CommandHandler, CallbackContext  # as tex

from functools import wraps

last_message = None

Update_Location_for = []
Send_Stats_for = []


def getConfiguration():
    config = configparser.ConfigParser()
    config.read('config.ini')
    global ttn_app_id, ttn_access_key, telegram_token, LIST_OF_ADMINS
    ttn_app_id = config.get("TTN", "app_id")
    ttn_access_key = config.get("TTN", "access_key")
    telegram_token = config.get("Telegram", "token")

    tmp=config.get("Telegram","admins").split(",")
    LIST_OF_ADMINS=[]
    for t in tmp:
        LIST_OF_ADMINS.append(int(t))
    print(LIST_OF_ADMINS)

    global telegram_bot, watch, live

    telegram_bot = telegram.Bot(telegram_token)
    watch = Watchdog(telegram_bot)
    live = LiveLocation()


def restricted(func):
    @wraps(func)
    def wrapped(update, context, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in LIST_OF_ADMINS:
            print("Unauthorized access denied for {}.".format(user_id))
            update.message.reply_text(
                "Sorry you're not invited to this party :,(")
            return
        return func(update, context, *args, **kwargs)
    return wrapped


def ttn_uplink_callback(msg, client):
    print("Received LoraWan uplink: ")  # , json.dumps(msg))
    global last_message
    last_message = msg
    count = len(msg.metadata.gateways)
    nachricht = 'New uplink by ' + \
        str(count) + ' Gateway' + ('s' if count > 1 else '')
    for id in Send_Stats_for:
        telegram_bot.send_message(id, nachricht)
    try:
        live.update(last_message.payload_fields.lat,
                    last_message.payload_fields.lon)
    except:
        pass
    watch.update()


@restricted
def sendLastLocation(update: telegram.Update, context: CallbackContext) -> None:
    if last_message is None:
        update.message.reply_text("No packet recived yet")
        return
    try:
        update.message.reply_text(
            "alt: " + str(last_message.payload_fields.alt))
        print("lat ", last_message.payload_fields.lat,
              " lng ", last_message.payload_fields.lon)
        update.message.reply_location(
            last_message.payload_fields.lat, last_message.payload_fields.lon)
    except:
        print("no position data")
        update.message.reply_text("No location recived yet")


@restricted
def sendLiveLocation(update: telegram.Update, context: CallbackContext) -> None:
    arg = update.message.text[6:]
    live.add(update, 60 * (int(arg) if arg.isdigit() else 10))


@restricted
def sendStats(update: telegram.Update, context: CallbackContext) -> None:
    id = update.message.chat.id
    if id in Send_Stats_for:
        Send_Stats_for.remove(id)
        update.message.reply_text("stop sending statistics")
    else:
        Send_Stats_for.append(id)
        update.message.reply_text(
            "sending statistics until /stats is called again")


@restricted
def sendWatchdog(update: telegram.Update, context: CallbackContext) -> None:
    arg = update.message.text[7:]
    watch.toggle(update.message.chat.id, int(arg) if arg.isdigit() else 600)


def main():
    """Config"""
    getConfiguration()

    """TTN"""
    handler = ttn.HandlerClient(ttn_app_id, ttn_access_key)
    # using mqtt client
    mqtt_client = handler.data()
    mqtt_client.set_uplink_callback(ttn_uplink_callback)
    mqtt_client.connect()

    """Telegram"""
    # Create the Updater and pass it your bot's token.
    updater = telegram.ext.Updater(telegram_token)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", sendLastLocation))
    dispatcher.add_handler(CommandHandler("pos", sendLastLocation))
    dispatcher.add_handler(CommandHandler("live", sendLiveLocation))
    dispatcher.add_handler(CommandHandler("stats", sendStats))
    dispatcher.add_handler(CommandHandler("watch", sendWatchdog))
    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
