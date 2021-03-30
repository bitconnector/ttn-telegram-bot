import telegram


class Location():
    def __init__(self, lat=0, lng=0):
        self.lat = lat
        self.lng = lng
        self.valid = False

    def update(self, lat, lng):
        self.lat = lat
        self.lng = lng
        self.valid = True


class LiveLocation(Exception):
    def __init__(self):
        self.messages = []
        self.loc = Location(0, 0)

    def sendLocation(self):
        print("update: ", self.messages)
        for msg in self.messages:
            msg.edit_live_location(self.loc.lat, self.loc.lng)
            try:
                msg.edit_live_location(self.loc.lat, self.loc.lng)
            except:
                Update_Location_for.remove(msg)
                print("remove user")

    def update(self, lat, lng):
        self.loc.update(lat, lng)
        self.sendLocation()

    def add(self, update: telegram.Update, timeout=3600):
        msg = update.message.reply_location(
            self.loc.lat, self.loc.lng, live_period=timeout)
        self.messages.append(msg)
