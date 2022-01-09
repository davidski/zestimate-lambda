#!/bin/env python

from __future__ import print_function

import boto3
import os
import logging
import pandas as pd
import requests
from dateutil.parser import parse
from s3fs.core import S3FileSystem
from datetime import datetime, timezone

# set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

zaddress = os.environ['zaddress']
zwsid = os.environ['zwsid']
bucket_name = os.getenv('bucket_name')
bucket_key = os.getenv('bucket_key')
sns_topic_arn = os.getenv('sns_topic_arn')


def lambda_handler(event, context):
    """ Main Lambda event handling loop """
    # read in CSV from S3
    s3fs = S3FileSystem(anon=False)
    data = pd.read_csv(s3fs.open('{}/{}'.format(bucket_name, bucket_key), mode='rb'), index_col=False)

    # fetch Zestimate
    url = 'https://api.bridgedataoutput.com/api/v2/zestimates_v2/zestimates?access_token=' + \
          zwsid + '&limit=1&near=' + zaddress
    response = requests.get(url)

    if response.status_code != 200:
        logger.fatal("Received unexpected response (%s) from Zillow API" %
                     response.status_code)
        return

    # parse response
    json_resp = response.json()
    zestimate_resp = json_resp['bundle'][0]

    zestimate = zestimate_resp['zestimate']
    zestimate_updated = zestimate_resp['timestamp']
    zestimate_high = zestimate_resp['lowPercent']
    zestimate_low = zestimate_resp['highPercent']
    rent_zestimate = zestimate_resp['rentalZestimate']
    rent_high = zestimate_resp['rentalLowPercent']
    rent_low = zestimate_resp['rentalHighPercent']
    rent_updated = zestimate_resp['rentalTimestamp']
    logger.info("Zestimate as of %s: %s" % (zestimate_updated, zestimate))

    # is last update of Zestimate > last date in CSV?
    if parse(zestimate_updated, ignoretz=True).date() <= parse(data.iloc[-1, 0]).date():
        logger.info("No update necessary - %s is not newer than %s. Exiting..." %
                    (parse(zestimate_updated), parse(data.iloc[-1, 0])))
        return

    # send message to SNS
    client = boto3.client('sns')
    response = client.publish(
        TopicArn=sns_topic_arn,
        Subject='Zestimate Updated',
        Message='Current zestimate is ' + '${:,.0f}'.format(int(zestimate)) +
                ' (change of ' + '${:,.2f}'.format(int(zestimate) - int(data.iloc[-1, 2])) + '). ' +
                'Low-High: {:,.0f} - {:,.0f}.'.format(int(zestimate_low), int(zestimate_high))
    )

    logger.info("Sent message %s to topic %s" %
                (response['MessageId'], sns_topic_arn))

    # append Zestimate to data frame
    data.loc[len(data)] = [zestimate_updated, zestimate_high, zestimate,
                           zestimate_low, rent_high, rent_zestimate, rent_low]

    # write to S3
    csv_body = data.to_csv(None, index=False)
    s3 = boto3.client('s3')
    s3.put_object(Bucket=bucket_name, Key=bucket_key, Body=csv_body)


if __name__ == '__main__':
    lambda_handler(event={'Records': [{'Sns': {'Message': 'foo'}}]},
                   context="")
