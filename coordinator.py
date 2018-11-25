import worker

import boto3
import json
import os
import logging
import time
import traceback

# {"Start": "2018-10-30T00:00:00", "End": "2018-10-30T00:59:59"}

if __name__ == "__main__":
    try:
        client = boto3.client('sqs', region_name='us-east-1')
        sqsUrl = client.get_queue_url(QueueName = "infrastructure-crawler-sqs-useast1.fifo")['QueueUrl']
        while(True):
            response = client.receive_message(QueueUrl=sqsUrl, MaxNumberOfMessages=1)
            messages = response.get('Messages')
            if (messages == None):
                break
            msg = messages[0]
            body = json.loads(msg['Body'])
            receiptHandle = msg['ReceiptHandle']
            start = body['Start']
            end = body['End']
            worker = worker.Worker(start, end)
            worker.run()
            os.system("aws s3 cp /data s3://infrastructure-storages-useast1-s3bucket/data/ --recursive")
            client.delete_message(QueueUrl = sqsUrl, ReceiptHandle = receiptHandle)
    except Exception:
        logging.error("Got an exception")
        logging.error(traceback.print_exc())
    finally:
        os.system("aws s3 cp /data s3://infrastructure-storages-useast1-s3bucket/data/ --recursive")


    # worker = worker.Worker("2018-10-30T00:00:00", "2018-10-30T23:59:59")
    # worker.run()