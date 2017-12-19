from flask import Flask, render_template, request, redirect
import datetime
import logging
import boto3
from flask_wtf import FlaskForm
from wtforms import IntegerField, TextAreaField
from wtforms.validators import DataRequired, NumberRange
import argparse
import os
import random
import string
import requests


parser = argparse.ArgumentParser(description='Command-line arguments.')
parser.add_argument('--debug', help='output debug messages', action='store_true')
parser.add_argument('--port', help='port number to listen on', nargs='?', default=5000, type=int)
parser.add_argument('--profile', help='AWS profile to use', nargs='?', type=str)
args = parser.parse_args()
if args.debug:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

logging.info("Creating Flask application.")
application = Flask(__name__)
application.secret_key = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(30))


# ideally, get the region of the instance in order to pass it to the boto3 Session
#r = requests.get('http://169.254.169.254/latest/dynamic/instance-identity/document')
region = 'us-east-1'

if args.profile:
    session = boto3.Session(profile_name=args.profile)
else:
    session = boto3.Session(region_name=region)
ssm = session.client('ssm')


class ParameterForm(FlaskForm):
    percentile = IntegerField('Percentile Threshold', default=50, validators=[DataRequired(), NumberRange(min=1, max=100)])
    channels = TextAreaField('Slack Channels', default=" ", validators=[])
    users = TextAreaField('Slack Users', default=" ", validators=[])


def set_config_value(key, value):
    print("Set config value {}: {}".format(key, value))
    response = ssm.put_parameter(Name=key, Value=value, Type='String', Overwrite=True)
    return response


def get_config_value(key, default=None):
    response = ssm.get_parameter(Name=key, WithDecryption=False)
    print("response: {}".format(response))
    if 'Parameter' in response:
        return response['Parameter'].get('Value') or default

    return default


@application.template_filter('strftime')
def _jinja2_filter_datetime(value, fmt='%Y-%m-%d %H:%M:%S'):
    return datetime.datetime.fromtimestamp(value).strftime(fmt)


@application.route("/", methods=['GET'])
def index_page():
    form = ParameterForm()

    percentile = get_config_value('CSVPercentileThreshold')
    form.percentile.data = percentile
    slack_channels = get_config_value('CSVNotifySlackChannels')
    form.channels.data = slack_channels
    slack_users = get_config_value('CSVNotifySlackUsers')
    form.users.data = slack_users

    context = {
        'form': form,
        'percentile_threshold': percentile,
        'slack_channels': slack_channels,
        'slack_users': slack_users,
        'page_update_time': datetime.datetime.now(),
    }
    return render_template("index.html", **context)


@application.route("/update", methods=['POST'])
def update_form():
    form = ParameterForm()
    if form.validate_on_submit():
        percentile = form.percentile.data
        set_config_value('CSVPercentileThreshold', str(percentile))
        channels = str(form.channels.data).strip()
        if len(channels) == 0:
            channels = " "
        set_config_value('CSVNotifySlackChannels', str(channels))
        users = str(form.users.data).strip()
        if len(users) == 0:
            users = " "
        set_config_value('CSVNotifySlackUsers', str(users))

    return redirect('/')


if __name__ == "__main__":
    # start the app
    logging.info("Starting app on port {}.".format(args.port))
    application.debug = True
    application.run(host='0.0.0.0', port=args.port)
