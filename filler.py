import worker

import boto3
import argparse
import time
import datetime
import os
import calendar
import random
import string

def generate_random_string(length):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

if __name__ == "__main__":
    # parser = argparse.ArgumentParser(description = "parse intervals")
    # parser.add_argument()
    secInDay = 86399.0
    end = (datetime.datetime.fromtimestamp(time.time()) - datetime.timedelta(days=1)).strftime("%Y-%m-%d") + "T23:59:59"
    start = (datetime.datetime.strptime(end, worker.DEFAULT_FORMAT) - datetime.timedelta(days=31) + datetime.timedelta(seconds=1)).strftime(worker.DEFAULT_FORMAT)
    latest = os.popen("aws s3 ls s3://infrastructure-storages-useast1-s3bucket/data/ | awk '{print $4}' | tail -n 1").readlines()

    if (len(latest) == 0):
        latest = start
    else:
        latest = (datetime.datetime.strptime(latest[0][:19], worker.DEFAULT_FORMAT) + datetime.timedelta(seconds=1)).strftime(worker.DEFAULT_FORMAT)
    epochEnd = calendar.timegm(time.strptime(end, worker.DEFAULT_FORMAT))
    epochStart = calendar.timegm(time.strptime(start, worker.DEFAULT_FORMAT))
    epochLatest = calendar.timegm(time.strptime(latest, worker.DEFAULT_FORMAT))

    client = boto3.client('sqs')
    sqsUrl = client.get_queue_url(QueueName="infrastructure-crawler-sqs-useast1.fifo")['QueueUrl']

    while (epochStart < epochEnd):
        localEnd = epochStart + secInDay

        msg = '{{ "Start": "{0}", "End": "{1}" }}'.format(time.strftime(worker.DEFAULT_FORMAT, time.gmtime(epochStart)),
                                                      time.strftime(worker.DEFAULT_FORMAT, time.gmtime(localEnd))
                                                      )
        response = client.send_message(QueueUrl = sqsUrl, MessageBody = msg, MessageGroupId = generate_random_string(10))
        print(msg)

        epochStart = localEnd + 1

    minDelta = datetime.timedelta(days=1)
    end = time.time()
    delta = datetime.timedelta(days=31)
    start = (datetime.datetime.fromtimestamp(end) - delta).timestamp()



