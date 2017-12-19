from __future__ import print_function

import json
import urllib
import boto3
import httplib


db = boto3.client('dynamodb')
ssm = boto3.client('ssm')


def get_config_value(key, default=None):
    response = ssm.get_parameter(Name=key, WithDecryption=False)
    print("response: {}".format(response))
    if 'Parameter' in response:
        return response['Parameter'].get('Value') or default

    return default


def lookup_user_list(slack_token):
    print("looking up user list")
    c = httplib.HTTPSConnection('slack.com')
    headers = {
        'Authorization': 'Bearer {}'.format(slack_token),
    }
    c.request('GET', '/api/users.list',
              headers=headers)
    r = c.getresponse()
    data = r.read()
    c.close()

    user_list = {}
    j = json.loads(data)
    if 'members' in j:
        for m in j['members']:
            user_list[m['name']] = m['id']

    return user_list


def send_slack_message(payload, slack_token):
    print("send slack message: {}, token: {}".format(payload, slack_token))
    c = httplib.HTTPSConnection('slack.com')
    headers = {
        'Authorization': 'Bearer {}'.format(slack_token),
        'Content-type': 'application/json; charset=utf8',
    }
    c.request('POST', '/api/chat.postMessage',
              body=json.dumps(payload),
              headers=headers)
    r = c.getresponse()
    data = r.read()
    print("data: {}".format(data))
    c.close()


def notify_slack_channel(channel_id, message, slack_token):
    payload = {
        'channel': '#{}'.format(channel_id),
        'text': message,
    }
    send_slack_message(payload, slack_token)


def notify_slack_user(user_id, message, slack_token):
    payload = {
        'channel': user_id,
        'text': message,
    }
    send_slack_message(payload, slack_token)


def lambda_handler(event, context):
    print("Received event: " + json.dumps(event, indent=2))

    slack_channels = get_config_value('CSVNotifySlackChannels', default='').split(',')
    #print("slack_channels: {}".format(slack_channels))
    slack_users = get_config_value('CSVNotifySlackUsers', default='').split(',')
    #print("slack_users: {}".format(slack_users))
    slack_token = get_config_value('CSVNotifySlackToken', default='xyz')
    #print("slack_token: {}".format(slack_token))

    file = str(event['Records'][0]['dynamodb']['NewImage']['Name']['S'])
    #print("file: {}".format(file))
    status = str(event['Records'][0]['dynamodb']['NewImage']['Status']['S'])
    #print("status: {}".format(status))

    # send status of run to Slack
    message = "Processing run for CSV file {} completed with status: {}".format(file, status)
    #print("message: {}".format(message))
    for c in slack_channels:
        notify_slack_channel(c, message, slack_token)
    user_list = lookup_user_list(slack_token)
    #print("user_list: {}".format(user_list))
    for u in slack_users:
        uid = user_list.get(u)
        #print("uid: {}".format(uid))
        if uid:
            notify_slack_user(uid, message, slack_token)
        else:
            print("User not found for name {}".format(u))
