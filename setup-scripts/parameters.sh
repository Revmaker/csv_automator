#!/bin/bash

# CSVPercentileThreshold
# - desc: Threshold percentile value for CSV processing
# - type: string
# - value: 51

aws ssm put-parameter --name CSVPercentileThreshold --description 'Threshold percentile value for CSV processing' --value 51 --type String --overwrite

# CSVNotifySlackChannels
# - desc: Slack channel names to notify when a CSV is processed
# - type: string
# - value: " "

aws ssm put-parameter --name CSVNotifySlackChannels --description 'Slack channel names to notify when a CSV is processed' --value " " --type String --overwrite

# CSVNotifySlackUsers
# - desc: Slack users to notify when a CSV is processed
# - type: string
# - value: " "

aws ssm put-parameter --name CSVNotifySlackUsers --description 'Slack users to notify when a CSV is processed' --value " " --type String --overwrite

# CSVNotifySlackToken
# - desc: OAuth token for communicating with Slack
# - type: string
# - value: "xyz"

aws ssm put-parameter --name CSVNotifySlackToken --description 'OAuth token for communicating with Slack' --value "xyz" --type String --overwrite
