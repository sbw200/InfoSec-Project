# Lesson 10: Information Disclosure Through Improper Error Handling

## Project Summary

This lesson demonstrates an information disclosure vulnerability in the DVSA application caused by improper error handling. Backend Lambda functions returned raw exception details to the client when malformed or incomplete requests were sent.

The exposed errors included stack traces, file paths, function names, line numbers, and internal exception messages. This gives attackers useful information about backend implementation details and system architecture.

## Learning Goals

- Demonstrate how raw backend errors leak sensitive implementation details
- Show how malformed requests can expose Lambda stack traces
- Identify missing exception handling in backend functions
- Return sanitized error responses to users
- Log detailed errors internally without exposing them to clients

## Repository Layout

```text
Lesson10/
|-- README.md
|-- Lesson10Report.docx
|-- evidence/
|   |-- image.png
|   `-- image copy.png
`-- fix/
    |-- image.png
    `-- order_shipping.py
```

## Vulnerability Summary

**Vulnerability:** Information Disclosure through unhandled exceptions

**Affected components:**

- API Gateway `/order` endpoint
- AWS Lambda backend functions
- `order_shipping.py`

**Root cause:** Missing exception handling and response sanitization.

When backend code raised an exception, the system returned the raw exception output directly to the client instead of returning a generic error message. This exposed internal implementation details that should only be available in server-side logs.

## Why This Works

The vulnerable backend did not consistently catch exceptions before returning responses. When a malformed request omitted required fields, the Lambda function attempted to access missing request data and raised an exception.

Because the exception was not sanitized, the client received details such as:

- internal file paths
- stack traces
- backend function names
- line numbers
- Python exception type and message

This information can help attackers understand the backend structure and plan further attacks.

## Environment and Tools

The vulnerability was tested against a deployed DVSA environment in AWS.

Components:

- frontend hosted as an S3 static website
- API Gateway routing requests to Lambda
- Lambda order-processing functions
- `/order` API endpoint

Tools used:

- Postman
- Browser Developer Tools
- AWS CloudWatch Logs

## Reproducing the Vulnerability

### 1. Send a Malformed Shipping Request

Send a request using the `shipping` action but omit the required `orderId` field.

Expected vulnerable behavior:

- the backend attempts to access the missing key
- the Lambda function raises a `KeyError`
- the API returns raw error details to the client

### 2. Review the API Response

The response exposed internal details, including:

```text
errorType: KeyError
errorMessage: "orderId"
/var/task/order_shipping.py
```

The response also included a full stack trace and the line of code that caused the error.

Evidence:

- [`evidence/image.png`](evidence/image.png)
- [`evidence/image copy.png`](<evidence/image copy.png>)

## Evidence and Proof

The vulnerability is confirmed by the raw error response returned to the client.

The exposed response included:

- `errorType: KeyError`
- `errorMessage: "orderId"`
- full stack trace
- internal file path `/var/task/order_shipping.py`
- line number and code context

This confirms that internal backend error details were exposed directly to users.

## Fix Strategy

The fix is to handle exceptions inside Lambda functions and return sanitized responses to clients.

Required mitigations:

- wrap risky backend logic in `try` / `except` blocks
- validate required fields before accessing them
- log detailed exceptions internally, such as to CloudWatch
- return generic error messages to the client
- avoid exposing stack traces, file paths, or line numbers in API responses

Example safe client response:

```json
{
  "status": "err",
  "msg": "An error occurred while processing the request"
}
```

## Code and Configuration Changes

The fix was applied to the Lambda function handling shipping updates.

Fixed file:

- [`fix/order_shipping.py`](fix/order_shipping.py)

The updated implementation wraps backend logic in exception handling:

```python
try:
    orderId = event["orderId"]
    address = event["shipping"]
    userId = event["user"]
    # normal processing continues
except Exception as e:
    print(e)
    return {"status": "err", "msg": "something went wrong oops"}
```

The important behavior change is that detailed errors are printed to logs for internal review, while the client receives a generic error response.

Evidence:

- [`fix/image.png`](fix/image.png)

## Verification After Fix

After applying the fix, the same malformed request was sent again.

Post-fix behavior:

- the system returned a generic error message
- no stack trace was exposed
- no internal file path was exposed
- no code line or backend implementation detail was returned
- detailed errors remained available only in CloudWatch logs

This confirms that the information disclosure issue was mitigated.

## Security Analysis

### Intended Security Rules

- Errors must not reveal internal implementation details
- Stack traces must not be exposed to users
- File paths and code line numbers must remain internal
- Detailed debugging information should be logged server-side only

### Behavior Trace

| State | Observed Behavior |
|---|---|
| Normal behavior | Valid requests return clean responses |
| Exploit behavior | Malformed requests expose stack traces, file paths, and backend logic |
| Post-fix behavior | Malformed requests return generic errors while details are logged internally |

### Deviation

The vulnerable behavior deviates from secure error-handling design because backend implementation details are exposed directly to the user.

**Deviation class:** unintentional information disclosure due to improper error handling

## Structured Summary

| Vulnerability | Intended Rule | Artifacts Used | Normal Behavior Evidence | Exploit Behavior Evidence |
|---|---|---|---|---|
| Unhandled Exceptions / Information Disclosure | Errors must not expose internal details or stack traces | API error response, stack trace, file path `/var/task/order_shipping.py` | Clean response without internal details | `KeyError` returned with stack trace, file path, and code line exposed |

| Vulnerability | Why This Is a Deviation | Deviation Class | Fix Applied | Post-Fix Verification |
|---|---|---|---|---|
| Unhandled Exceptions | System returns raw backend errors revealing sensitive information | Unintentional information disclosure | Backend Lambda error handling with `try` / `except` and response sanitization | Only generic error messages returned |

## Takeaway

This lesson shows that error handling is part of the security boundary. Even when application logic is otherwise correct, raw errors can expose implementation details that make future attacks easier.

Secure applications should log detailed errors internally and return sanitized responses externally. Stack traces, file paths, function names, and code snippets should never be exposed to users.

## Report Reference

The original report and screenshots remain in [`Lesson10Report.docx`](Lesson10Report.docx), [`evidence/`](evidence/), and [`fix/`](fix/). Those files were not modified.
