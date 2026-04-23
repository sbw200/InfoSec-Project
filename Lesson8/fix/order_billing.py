import json
import urllib3
import boto3
import os
import time
import decimal
from decimal import Decimal
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
    print(json.dumps(event))

    class DecimalEncoder(json.JSONEncoder):
        def default(self, o):
            if isinstance(o, decimal.Decimal):
                if o % 1 > 0:
                    return float(o)
                else:
                    return int(o)
            return super(DecimalEncoder, self).default(o)

    orderId = event["orderId"]
    userId = event["user"]
    http = urllib3.PoolManager()

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ["ORDERS_TABLE"])

    key = {
        "orderId": orderId,
        "userId": userId
    }

    # ✅ STEP 1: ATOMIC LOCK (open → processing)
    try:
        table.update_item(
            Key=key,
            UpdateExpression="SET orderStatus = :processing",
            ConditionExpression="attribute_exists(orderId) AND attribute_exists(userId) AND orderStatus = :open",
            ExpressionAttributeValues={
                ":processing": 200,
                ":open": 100
            }
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return {"status": "err", "msg": "order already made or currently processing"}
        raise

    # ✅ STEP 2: FETCH ORDER AFTER LOCK
    response = table.get_item(
        Key=key,
        AttributesToGet=['orderId', 'orderStatus', 'itemList']
    )

    if 'Item' not in response:
        return {"status": "err", "msg": "could not find order"}

    # ✅ STEP 3: BUILD CART DATA
    data_dict = []
    for key_item, value in response["Item"]['itemList'].items():
        data_dict.append({"itemId": key_item, "quantity": int(value)})

    data = json.dumps(data_dict, cls=DecimalEncoder)

    # ✅ STEP 4: GET TOTAL
    url = os.environ["GET_CART_TOTAL"]
    clen = len(data)
    req = http.request("POST", url, body=data, headers={
        'Content-Type': 'application/json',
        'Content-Length': clen
    })
    res = json.loads(req.data)
    cartTotal = float(res['total'])
    missings = res.get("missing", {})

    # ✅ STEP 5: PROCESS PAYMENT
    url = os.environ["PAYMENT_PROCESS_URL"]
    billing_data = json.dumps(event["billing"])
    clen = len(billing_data)

    req = http.request("POST", url, body=billing_data, headers={
        'Content-Type': 'application/json',
        'Content-Length': clen
    })

    res = json.loads(req.data)
    ts = int(time.time())

    if res['status'] == 110:
        return {"status": "err", "msg": "invalid payment details"}

    elif res['status'] == 120:

        update_expression = 'SET orderStatus = :orderstatus, paymentTS = :paymentTS, totalAmount = :total, confirmationToken = :token'

        TWOPLACES = Decimal(10) ** -2

        expression_attributes = {
            ':orderstatus': res['status'],
            ':paymentTS': ts,
            ':total': Decimal(cartTotal).quantize(TWOPLACES),
            ':token': res['confirmation_token'],
            ':processing': 200
        }

        # HANDLE MISSING ITEMS
        if missings:
            new_item_list = {}
            response = table.get_item(Key=key)
            items = response.get("Item", {}).get("itemList", {})

            for item in items:
                new_item_list[item] = items[item] - missings[item] if missings.get(item) else items[item]

            expression_attributes[":il"] = new_item_list
            update_expression += ', itemList = :il'

        try:
            # ✅ STEP 6: FINALIZE ONLY IF STILL PROCESSING
            table.update_item(
                Key=key,
                UpdateExpression=update_expression,
                ConditionExpression="orderStatus = :processing",
                ExpressionAttributeValues=expression_attributes
            )

            # SEND MESSAGE TO SQS
            sqs = boto3.client('sqs')
            sqs.send_message(
                QueueUrl=os.environ["SQS_URL"],
                MessageBody=json.dumps({"orderId": orderId, "userId": userId}),
                DelaySeconds=10
            )

            return {
                "status": "ok",
                "amount": float(cartTotal),
                "token": res['confirmation_token'],
                "missing": missings
            }

        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                return {"status": "err", "msg": "order state changed during billing"}
            raise

    else:
        return {"status": "err", "msg": "could not process payment"}