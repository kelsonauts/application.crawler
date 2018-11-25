import custom_statistic

import time
import requests
import calendar
import json
import logging
import sys

DEFAULT_MAX_STEP_SIZE = 60 * 60 # in seconds
DEFAULT_MIN_STEP_SIZE = 225 # in seconds
DEFAULT_MAX_PAGES = 20
DEFAULT_MAX_REC_PER_PAGE = 100
DEFAULT_MAX_REC_RETURNED = 2000
DEFAULT_DELAY = 0 # to avoid limit in 10 requests per sec per ip
DEFAULT_FORMAT = "%Y-%m-%dT%H:%M:%S"
DEFAULT_REQUEST_ATTEMPTS = 10
DEFAULT_BATCH_SIZE = 3000
DEFAULT_PATH = "/data/"
DEFAULT_LOG_PATH = "/data/"
DEFAULT_ENCODING = 'utf8'
DEFAULT_MESSAGE_PERIOD = 100

# Получаем time в виде строки "YYYY-MM-DDTHH-mm-ss". Преобразуем в объект time
# Запускаем на всем интевале, если found


# This class uses epoch time format "YYYY-MM-DDTHH-mm-ss". Times stores as ints
class Worker:
    stepSize = None #In seconds
    startInterval = None
    endInterval = None
    startLocalInterval = None
    endLocalInterval = None
    ids = []
    counter = 0 #
    statistic = None
    logger = None
    totalRecordsAmount = 0

    def __del__(self):
        self.stepSize = None  # In seconds
        self.startInterval = None
        self.endInterval = None
        self.startLocalInterval = None
        self.endLocalInterval = None
        del self.ids[:]
        self.counter = 0  #
        self.statistic = None
        self.logger = None
        self.totalRecordsAmount = 0

    def __init__(self, startInterval, endInterval, logger = None, stepSize = DEFAULT_MAX_STEP_SIZE):
        if (stepSize < DEFAULT_MIN_STEP_SIZE or stepSize > DEFAULT_MAX_STEP_SIZE):
            raise Exception(("Size step '{0}' must be larger than minimal step size '{1}' and it must be smaller than {2}".
                             format(stepSize, DEFAULT_MIN_STEP_SIZE, DEFAULT_MAX_STEP_SIZE)))

        if (startInterval == None):
            raise Exception(("Start of the interval must be set up"))

        if (endInterval == None):
            raise Exception(("End of the interval must be set up") )

        if ( time.strptime(startInterval, DEFAULT_FORMAT) > time.strptime( endInterval, DEFAULT_FORMAT ) ):
            raise Exception( "Start of interval '{0}' must be less than end of interval '{1}'".format(startInterval, endInterval) )

        self.statistic = custom_statistic.Statistic()
        self.stepSize = stepSize
        self.startInterval = self.convert_time_to_epoch_seconds(self.build_formated_time(startInterval))
        self.endInterval = self.convert_time_to_epoch_seconds(self.build_formated_time(endInterval))
        self.counter = 0


        self.logger = logger

        if (self.logger == None):
            logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
            self.logger = logging.getLogger(endInterval)

            fileHandler = logging.FileHandler("{0}/{1}.log".format(DEFAULT_LOG_PATH, endInterval).replace(':', '-'))
            fileHandler.setFormatter(logFormatter)
            self.logger.addHandler(fileHandler)

            consoleHandler = logging.StreamHandler()
            consoleHandler.setFormatter(logFormatter)
            self.logger.addHandler(consoleHandler)
            self.logger.setLevel(logging.INFO)

    def api_req(self, body):
        if (not (self.counter < 10 )):
            time.sleep(DEFAULT_DELAY)
            self.counter = 0

        self.counter += 1
        tmp = requests.get(body)
        return tmp

    def api_req_safe(self, body):
        attemptsCounter = 0
        response = self.api_req(body)
        while( (response.status_code != 200) and (attemptsCounter < DEFAULT_REQUEST_ATTEMPTS)):
            self.statistic.incRequests("Bad")
            response = self.api_req(body)
            attemptsCounter += 1
        if attemptsCounter >= DEFAULT_REQUEST_ATTEMPTS:
            self.statistic.incRequests("Bad")
            self.statistic.send_extra_statistic({"Bad request": body, "Attempts": attemptsCounter, "Response status code": response.status_code, "Response body": response.json()})
            self.logger.debug("Amount of failed requests: {0}".format(self.statistic.badRequestsCounter))
        else:
            self.statistic.incRequests("Good")
        return response

    # Build time object with custom format from string with time in format "YYYY-MM-DDTHH:mm:ss", return time object
    def build_formated_time(self, timeStr):
        return time.strptime(timeStr, DEFAULT_FORMAT)

    # Convert string with time object from format "YYYY-MM-DDTHH:mm:ss" to epoch seconds and return int time
    def convert_time_to_epoch_seconds(self, time_r):
        return calendar.timegm(time_r)

    def get_formatted_hr_time_string(self, timeEpoch):
        return time.strftime(DEFAULT_FORMAT, self.get_formatted_hr_time_object(timeEpoch))

    def get_formatted_hr_time_object(self, timeEpoch):
        return time.gmtime(timeEpoch)

    # Returns time object shifted on stepSize, timeObj is epoch (int)
    def shift_time(self, timeObj, shiftForward = True):
        return (timeObj + self.stepSize) if shiftForward else (timeObj - self.stepSize)

    # Parse json and collect ids of vacancies
    def retrieve_ids(self, response):
        for iter in response:
            self.ids.append(iter['id'])

    def collect_pages(self, start, end):
        response = self.api_req_safe('https://api.hh.ru/vacancies?per_page={0}&page={1}&date_from={2}&date_to={3}'
                                .format(
                                        DEFAULT_MAX_REC_PER_PAGE,
                                        0,
                                        self.get_formatted_hr_time_string(start),
                                        self.get_formatted_hr_time_string(end))).json()
        pages = response['pages']
        for page in range(pages):
            response = self.api_req_safe('https://api.hh.ru/vacancies?per_page={0}&page={1}&date_from={2}&date_to={3}'
                                    .format(
                                            DEFAULT_MAX_REC_PER_PAGE,
                                            page,
                                            self.get_formatted_hr_time_string(start),
                                            self.get_formatted_hr_time_string(end))).json()
            self.retrieve_ids(response['items'])
        self.logger.info("Retrieved ids: {0} of {1}". format(len(self.ids), self.totalRecordsAmount))


    def check_found_records(self, response):
        return (response.json()['found'] <= DEFAULT_MAX_REC_RETURNED )

    def run(self):
        self.logger.info("Start retrieving vacancies id. Global interval for worker is: from {0} to {1}"
                         .format(self.get_formatted_hr_time_string(self.startInterval),
                                 self.get_formatted_hr_time_string(self.endInterval)))
        self.statistic.init_new_timer()
        response = self.api_req_safe('https://api.hh.ru/vacancies?per_page={0}&page={1}&date_from={2}&date_to={3}'
                                .format(
                                        DEFAULT_MAX_REC_PER_PAGE,
                                        0,
                                        self.get_formatted_hr_time_string(self.startInterval),
                                        self.get_formatted_hr_time_string(self.endInterval)))
        if (response.status_code != 200):
            self.logger.error("Failed to retrieve vacancies. ResponseCode: {0}. ResponseBody: {1}".format(response.status_code, response.json()))
        self.totalRecordsAmount = response.json()['found']
        self.logger.info("Records found: {0}".format(self.totalRecordsAmount))

        if ( self.check_found_records(response) == True ):
            self.collect_pages(self.startInterval, self.endInterval)
        else:
            self.startLocalInterval = self.endLocalInterval = self.startInterval
            stepCanChange = self.dec_step_size()

            resp = self.api_req_safe('https://api.hh.ru/vacancies?per_page={0}&page={1}&date_from={2}&date_to={3}'
                                .format(
                                        DEFAULT_MAX_REC_PER_PAGE,
                                        0,
                                        self.get_formatted_hr_time_string(self.startLocalInterval),
                                        self.get_formatted_hr_time_string(self.endLocalInterval)))

            while (self.endLocalInterval <= self.endInterval):
                self.startLocalInterval = self.endLocalInterval
                self.endLocalInterval = self.startLocalInterval + self.stepSize

                while (stepCanChange and  (resp.status_code == 200) and not(self.check_found_records(resp))):
                    stepCanChange = self.dec_step_size()
                    self.endLocalInterval = self.startInterval + self.stepSize

                    resp = self.api_req_safe(
                        'https://api.hh.ru/vacancies?per_page={0}&page={1}&date_from={2}&date_to={3}'
                            .format(
                            DEFAULT_MAX_REC_PER_PAGE,
                            0,
                            self.get_formatted_hr_time_string(self.startLocalInterval),
                            self.get_formatted_hr_time_string(self.endLocalInterval)))

                if (resp.status_code != 200):
                    continue

                self.collect_pages(self.startLocalInterval, self.endLocalInterval)

        self.statistic.send_statistic(self.get_formatted_hr_time_string(self.startInterval),
                                      self.get_formatted_hr_time_string(self.endInterval),
                                      len(self.ids))
        self.logger.info("Finish retrieving ids. Totally retrieved: {0} of {1}".format(len(self.ids), self.totalRecordsAmount))
        self.logger.info("Current step size: {0}, minimal step size: {1}, maximal step size {2}".format(self.stepSize, DEFAULT_MIN_STEP_SIZE, DEFAULT_MAX_STEP_SIZE))
        self.statistic.init_new_timer("Retrieving vacancies list")
        self.collect_vacancies()
        self.statistic.init_new_timer("Retrieving vacancies")
        self.__del__()

    def collect_vacancies(self):
        file = open(DEFAULT_PATH + self.get_formatted_hr_time_string(self.endInterval).replace(':', '-') + '.json', 'w')
        vacancies = []
        counter = 0
        dumpedCounter = 0
        for iter in self.ids:
            response = self.api_req_safe('https://api.hh.ru/vacancies/{0}'.format(iter))

            if (response.status_code != 200):
                continue

            vacancies.append(response.json())
            if (counter % 100 == 0):
                self.logger.info("Collected vacancies: {0} of {1}".format(dumpedCounter + counter, len(self.ids)))
            counter += 1

            # if (counter >= DEFAULT_BATCH_SIZE):
            #     file.write(json.dumps(vacancies, ensure_ascii = False))
            #     dumpedCounter += counter
            #     self.logger.info("Dumped vacancies: {0} of {1}".format(dumpedCounter, len(self.ids)))
            #     counter = 0
            #     vacancies = []

        if (counter > 0):
            # file.write("{ \"Items\": ")
            # file.write(json.dumps(vacancies, ensure_ascii = False))
            # file.write(", ")
            # file.write("\"Found\": {0}, \"Collected\": {1}, \"Statistic\": \"Statistic\"".format(self.totalRecordsAmount, len(self.ids)))
            # file.write("}")
            file.write("{{ \"Items\": {0}, \"Found\": {1}, \"Collected\": {2}, \"Statistic\": {3} }}"
                       .format(json.dumps(vacancies, ensure_ascii = False),
                               self.totalRecordsAmount,
                               len(self.ids),
                               self.statistic.to_json()))
            dumpedCounter += counter
            self.logger.info("Dumped vacancies: {0} of {1}".format(dumpedCounter, len(self.ids)))
            counter = 0
            vacancies = []
        self.logger.info("Dumping finished. Dumped vacanices: {0} of found {1}".format(dumpedCounter, self.totalRecordsAmount))




    def check_step_size(self, newStepSize):
        return not(newStepSize < DEFAULT_MIN_STEP_SIZE
                or newStepSize > DEFAULT_MAX_STEP_SIZE
                or (newStepSize - int(newStepSize) != 0)
                or (self.startLocalInterval + newStepSize) > self.endInterval)

    # Different policies can be applied
    def dec_step_size(self):
        newStepSize = self.fixed_step_dec(self.stepSize)

        if (not self.check_step_size(newStepSize)):
            return False
        else:
            self.stepSize = newStepSize
            return True

    def fixed_step_dec(self, oldStepSize):
        return (oldStepSize / 2)

    def fixed_step_inc(self, oldStepSize):
        return (oldStepSize * 2)

    def find_optimal_step_size(self):
        return 0
