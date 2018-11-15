import time
import calendar

class Statistic:
    goodRequestsCounter = 0
    badRequestsCounter = 0
    timeStart = None
    gotRecordsPerTimeInterval = []
    timeIntervals = []

    extraStats = [] #For collecting custom statistic not implemented in this class

    def init_new_timer(self, description = ""):
        if (self.timeStart != None):
            timeEnd = time.time()
            self.timeIntervals.append({"Start": self.timeStart, "End": timeEnd, "Description": description})
        self.timeStart = time.time() #In epoch seconds

    def reset_timer(self):
        self.timeStart = time.time()

    def incRequests(self, type):
        if type == "Good":
            self.goodRequestsCounter += 1
        elif type == "Bad":
            self.badRequestsCounter += 1
        else:
            raise Exception("Argument 'type': {0} must be either 'Good' or 'Bad'".format(type))

    def send_statistic(self, startInterval, endInterval, recAmount):
        self.timeIntervals.append((startInterval, endInterval, recAmount))

    def send_extra_statistic(self, body):
        self.extraStats.append(body)

    def to_json(self):
        tmp = {"GoodRequestCounter": self.goodRequestsCounter,
                  "BadRequestCounter": self.badRequestsCounter,
                  "RecordsPerTimeIntervals": self.gotRecordsPerTimeInterval,
                  "TimeIntervals": self.timeIntervals}
        return tmp