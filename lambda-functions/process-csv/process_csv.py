from __future__ import print_function

import json
import urllib
import boto3
#import scipy.stats as stats
import time


s3 = boto3.client('s3')
db = boto3.client('dynamodb')
ssm = boto3.client('ssm')


LENGTHS_TABLE_NAME = 'CSVLengths'


class InvalidFileType(Exception):
    """
    An exception that is raised when the incoming file is not of the correct type.
    """
    pass


def calc_percentile(series, value):
    """
    Determines the percentile score of the specified value in the provided series.
    """
    print("series: {}, value: {}".format(series, value))
    series.append(value)
    print("series: {}".format(series))
    series = sorted(list(set(series)))
    print("series: {}".format(series))
    series_length = len(series)
    print("series_length: {}".format(series_length))
    index = series.index(value) + 1
    print("index: {}".format(index))
    perc = float(index) / float(series_length)
    print("perc: {}".format(perc))

    return int(perc * 100.0)


def get_config_value(key, default=None):
    response = ssm.get_parameter(Name=key, WithDecryption=False)
    print("response: {}".format(response))
    if 'Parameter' in response:
        return response['Parameter'].get('Value') or default

    return default


def get_csv_lengths():
    response = db.scan(TableName=LENGTHS_TABLE_NAME,
                        AttributesToGet=[ 'Length' ],
                        Limit=500)
    print("response: {}".format(response))
    if 'Items' in response:
        #items = sorted(list(response['Items']), cmp=lambda x,y: cmp(int(x['Created']['N']), int(y['Created']['N'])))
        items = list(response['Items'])
        print("items: {}".format(items))
        values = map(lambda x: int(x['Length']['N']), items)
        print("values: {}".format(values))
        return values
    return []


def store_csv_length(name, length, status):
    print("name: {}, length: {}, status: {}".format(name, length, status))
    response = db.put_item(TableName=LENGTHS_TABLE_NAME,
                           Item={
                               'Name': {
                                    'S': name,
                               },
                               'Length': {
                                    'N': str(length),
                               },
                               'Status': {
                                    'S': status,
                               },
                               'Created': {
                                    'N': str(int(time.time())),
                               }
                           })
    print("response: {}".format(response))
    return response


def lambda_handler(event, context):
    #print("Received event: " + json.dumps(event, indent=2))

    # Get the object from the event and show its content type
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.unquote_plus(event['Records'][0]['s3']['object']['key'].encode('utf8'))
    try:

        # get desired percentile value
        percentile_threshold = int(get_config_value('CSVPercentileThreshold', default='50'))
        print("percentile_threshold: {}".format(percentile_threshold))

        # get object metadata
        response = s3.get_object(Bucket=bucket, Key=key)
        print("response: {}".format(response))
        # check type
        file_type = response['ContentType']
        print("file_type: {}".format(file_type))
        if file_type != 'text/csv':
            raise InvalidFileType, "File type was not 'text/csv': {}".format(file_type)

        csv_length = int(response['ContentLength'])
        print("csv_length: {}".format(csv_length))

        # calculate percentile of this CSV
        # - fetch previous CVS lengths (order by date)
        lengths = get_csv_lengths()
        # - if none and this is non-zero length, mark this a success and store length and date
        if len(lengths) == 0:
            status = 'SUCCESS'
        else:
            # is length below threshold?
            csv_percentile = calc_percentile(lengths, csv_length)
            print("csv_percentile: {}".format(csv_percentile))
            if csv_percentile >= percentile_threshold:
                status = 'SUCCESS'
            else:
                status = 'ERROR'

        # store record
        store_csv_length(key, csv_length, status)

    except Exception as e:
        print(e)
        print('Error getting object {} from bucket {}.'.format(key, bucket))
        raise e
