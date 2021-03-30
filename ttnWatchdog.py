from threading import Timer


class TTNWatchdog(Exception):
    def __init__(self, timeout, telegram_bot, telegram_id):  # timeout in seconds
        self.timeout = timeout
        self.telegram_bot = telegram_bot
        self.telegram_id = telegram_id
        self.timer = Timer(self.timeout, self.defaultHandler)
        self.timer.start()

    def start(self):
        try:
            self.timer.start()
        except:
            pass

    def stop(self):
        try:
            self.timer.cancel()
        except:
            pass

    def reset(self):
        if self.timer.is_alive() is False:
            nachricht = 'Got packets again'
            self.telegram_bot.send_message(self.telegram_id, nachricht)
        self.stop()
        self.timer = Timer(self.timeout, self.defaultHandler)
        self.start()

    def defaultHandler(self):
        nachricht = "Lost connection since {:.1f} Minutes".format(
            self.timeout / 60)
        self.telegram_bot.send_message(self.telegram_id, nachricht)


class Watchdog():
    def __init__(self, telegram_bot):
        self.telegram_bot = telegram_bot
        self.watchdogs = []

    def add(self, telegram_id, timeout):
        self.watchdogs.append(TTNWatchdog(
            timeout, self.telegram_bot, telegram_id))
        self.telegram_bot.send_message(telegram_id,
                                       "sending Watchdog warning if connection is lost for " +
                                       "{:.1f} Minutes until /watch is called again"
                                       .format(timeout / 60))

    def remove(self, telegram_id):
        watchdog = self.getWatchdog(telegram_id)
        watchdog.stop()
        self.telegram_bot.send_message(
            watchdog.telegram_id, "stop Watchdog")
        self.watchdogs.remove(watchdog)

    def toggle(self, telegram_id, timeout=60):
        watch = self.getWatchdog(telegram_id)
        if watch is None:
            self.add(telegram_id, timeout)
        else:
            self.remove(telegram_id)

    def update(self):
        for watch in self.watchdogs:
            watch.reset()

    def getWatchdog(self, telegram_id):
        for watch in self.watchdogs:
            if watch.telegram_id == telegram_id:
                return watch
        return None
