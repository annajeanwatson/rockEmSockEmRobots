
from sqs import *
import boto3
import json

with open('ec2_setup.json') as f:
    CONFIG = json.load(f)

# print(CONFIG)
node_config = CONFIG["nodes"][0]

sqs_resource = boto3.resource('sqs', region_name='us-east-2')
sqs_client = boto3.client('sqs', region_name='us-east-2')

send_sqs_message(sqs_resource, node_config["queue_url"], node_config["queue_name"], "Meow!2")

msg = retrieve_sqs_messages(sqs_client, node_config["queue_url"])
print(msg)