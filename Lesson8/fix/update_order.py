import json
import boto3
import os
from botocore.exceptions import ClientError

# status list
# -----------
# 100: open
# 110: payment-failed
# 120: paid
# 200: processing
# 210: shipped
# 300: delivered
# 500: cancelled
# 600: rejected

def lambda_handler(event, context):
    orderId = event["orderId"]
    itemList = event["items"]
    userId = event["user"]

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ["ORDERS_TABLE"])

    try:
        table.update_item(
            Key={"orderId": orderId, "userId": userId},
            UpdateExpression="SET itemList = :itemList",
            ConditionExpression="attribute_exists(orderId) AND attribute_exists(userId) AND orderStatus = :open",
            ExpressionAttributeValues={
                ":itemList": itemList,
                ":open": 100
            }
        )
        res = {"status": "ok", "msg": "cart updated"}

    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            res = {"status": "err", "msg": "order cannot be updated during processing or after payment"}
        else:
            raise

    return res