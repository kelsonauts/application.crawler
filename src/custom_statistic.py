import time
import json
import calendar

class Statistic:
    goodRequestsCounter = 0
    badRequestsCounter = 0
    timeStart = None
    gotRecordsPerTimeInterval = []
    timeIntervals = []

    extraStats = [] #For collecting custom statistic not implemented in this class

    def __del__(self):
        self.goodRequestsCounter = 0
        self.badRequestsCounter = 0
        self.timeStart = None
        del self.gotRecordsPerTimeInterval[:]
        del self.timeIntervals[:]

        self.extraStats = []  # For collecting custom statistic not implemented in this class

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
        self.gotRecordsPerTimeInterval.append({ "Start": startInterval, "End": endInterval, "RecAmount": recAmount})

    def send_extra_statistic(self, body):
        self.extraStats.append(body)

    def to_json(self):
        tmp = "{{ \"GoodRequestCounter\": {0}, \"BadRequestCounter\": {1}, \"RecordsPerTimeIntervals\": {2}, \"TimeIntervals\": {3} }}"\
            .format(self.goodRequestsCounter,
                    self.badRequestsCounter,
                    json.dumps(self.gotRecordsPerTimeInterval, ensure_ascii=False),
                    json.dumps(self.timeIntervals, ensure_ascii=False))
        # tmp = '{ "Object": "None" }'
        return tmp
