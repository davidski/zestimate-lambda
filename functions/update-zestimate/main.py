#!/bin/env python

from __future__ import print_function

import boto3
import os
import logging
import pandas as pd
import requests
from bs4 import BeautifulSoup
from dateutil.parser import parse

# set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

zpid = os.environ['zpid']
zwsid = os.environ['zwsid']
bucket_name = os.getenv('bucket_name')
bucket_key = os.getenv('bucket_key')
sns_topic_arn = os.getenv('sns_topic_arn')


def lambda_handler(event, context):
    """ Main Lambda event handling loop """
    # read in CSV from S3
    s3 = boto3.client('s3')
    obj = s3.get_object(Bucket=bucket_name, Key=bucket_key)
    data = pd.read_csv(obj['Body'], index_col=False)

    # fetch Zestimate
    url = 'http://www.zillow.com/webservice/GetZestimate.htm?zws-id=' + \
          zwsid + '&zpid=' + zpid + '&rentzestimate=TRUE'
    response = requests.get(url)

    if response.status_code != 200:
        logger.fatal("Received unexpected response (%s) from Zillow API" %
                     response.status_code)
        return

    # parse response
    soup = BeautifulSoup(response.text, "html.parser")
    zestimate = soup.zestimate.amount.string
    zestimate_updated = getattr(soup.zestimate, 'last-updated').text
    zestimate_high = soup.zestimate.high.text
    zestimate_low = soup.zestimate.low.text
    rent_zestimate = soup.rentzestimate.amount.text
    rent_high = soup.rentzestimate.high.text
    rent_low = soup.rentzestimate.low.text
    rent_updated = getattr(soup.rentzestimate, 'last-updated').text
    logger.info("Zestimate as of %s: %s" % (zestimate_updated, zestimate))

    # is last update of Zestimate > last date in CSV?
    if parse(zestimate_updated) <= parse(data.iloc[-1, 0]):
        logger.info("No update necessary - %s is not newer than %s. Exiting..." %
                    (parse(zestimate_updated), parse(data.iloc[-1, 0])))
        return

    # send message to SNS
    client = boto3.client('sns')
    response = client.publish(
        TopicArn=sns_topic_arn,
        Subject='Zestimate Updated',
        Message='Current zestimate is ' + '${:,.2f}'.format(int(zestimate)) +
                ' (' + '${:,.2f}'.format(int(data.iloc[-1, 2]) - int(zestimate)) + ' )'
    )

    logger.info("Sent message %s to topic %s" %
                (response['MessageId'], sns_topic_arn))

    # append Zestimate to data frame
    data.loc[len(data)] = [zestimate_updated, zestimate_high, zestimate,
                           zestimate_low, rent_high, rent_zestimate, rent_low]

    # write to S3
    csv_body = data.to_csv(None, index=False)
    s3.put_object(Bucket=bucket_name, Key=bucket_key, Body=csv_body)


if __name__ == '__main__':
    lambda_handler(event={'Records': [{'Sns': {'Message': 'foo'}}]},
                   context="")
