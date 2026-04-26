# Lesson 1 and Lesson 9: Event Injection and Vulnerable Dependencies

## Project Summary

This folder documents an Event Injection vulnerability in the DVSA application caused by unsafe deserialization of attacker-controlled input. The vulnerable backend Lambda function handled API Gateway requests by deserializing request data with `node-serialize`, which allowed malicious serialized functions to execute inside the Lambda runtime.

Lesson 9 connects this exploit to vulnerable dependency management. The exploit works because the application used the vulnerable `node-serialize` package, and the broader dependency set also included risky libraries such as `node-jose`.

## Learning Goals

- Demonstrate how unsafe deserialization can become remote code execution
- Show how attacker-controlled request data can execute inside AWS Lambda
- Connect the exploit to vulnerable third-party dependencies
- Replace unsafe deserialization with safe JSON parsing
- Validate that the malicious payload no longer executes after the fix

## Repository Layout

```text
Lesson1 and Lesson9/
|-- README.md
|-- Lesson1andLesson9Report.docx
`-- fix/
    `-- order-manager.js
```

## Vulnerability Summary

**Vulnerability:** Event Injection / unsafe deserialization

**Affected component:** AWS Lambda request-processing logic behind API Gateway

**Root cause:** The backend used `node-serialize` on untrusted request data:

```javascript
var req = serialize.unserialize(event.body);
var headers = serialize.unserialize(event.headers);
```

The `node-serialize` library supports the `$$ND_FUNC$$` pattern, which can reconstruct and execute serialized functions. Because the request body came from the user and was not validated before deserialization, an attacker could inject a function into the request body and cause code execution during request parsing.

## Environment and Tools

The vulnerability was tested against a deployed DVSA environment in AWS:

- Frontend hosted as an S3 static website
- API exposed through Amazon API Gateway
- Backend implemented with AWS Lambda functions
- Primary endpoint: `/dvsa/order`

Tools used:

- Browser DevTools
- Postman
- AWS CloudWatch Logs

## Reproducing the Vulnerability

### 1. Send a Normal Request

Send a valid order request to the API endpoint:

```json
{
  "action": "orders"
}
```

Expected vulnerable-app behavior:

- The backend processes the request normally
- The API returns the user's order data

### 2. Send a Malicious Serialized Payload

Modify the request body by adding a malicious serialized function payload:

```json
{
  "action": "orders",
  "test": "_$$ND_FUNC$$_function(){throw 'INJECTEDbyMK'}()"
}
```

Expected vulnerable-app behavior:

- The API returns a `502 Bad Gateway` error
- The Lambda function fails internally

### 3. Check CloudWatch Logs

Open the CloudWatch logs for the Lambda function that handled the request.

Evidence of exploitation:

```text
errorMessage: INJECTEDbyMK
```

The exact attacker-controlled string appears in the Lambda error output, proving that the injected function executed inside the backend runtime.

## Evidence and Proof

The vulnerability is confirmed by the behavior difference between normal and malicious requests:

| Test | Observed Behavior |
|---|---|
| Normal request | Valid response with order data |
| Malicious request | Backend failure and `502 Bad Gateway` |
| CloudWatch review | Injected string `INJECTEDbyMK` appears in Lambda logs |

This proves that the backend treated user-controlled request data as executable content instead of plain data.

## Fix Strategy

The fix is to remove unsafe deserialization from the request path. Request bodies should be treated strictly as JSON and parsed using safe JSON parsing. Input fields should also be validated against expected actions, data types, and formats.

Unsafe behavior removed:

```javascript
var req = serialize.unserialize(event.body);
var headers = serialize.unserialize(event.headers);
```

Safe replacement:

```javascript
var req = JSON.parse(event.body || "{}");
var headers = event.headers || {};
```

The fixed handler is stored in [`fix/order-manager.js`](fix/order-manager.js).

## Main Code Changes

- Removed unsafe request-body deserialization using `node-serialize`
- Parsed request bodies as JSON with `JSON.parse`
- Treated headers as normal API Gateway header objects
- Prevented user-controlled request content from being interpreted as JavaScript code

## Verification After Fix

After applying the fix, the same exploit payload was sent again:

```json
{
  "action": "orders",
  "test": "_$$ND_FUNC$$_function(){throw 'INJECTEDbyMK'}()"
}
```

Post-fix expected behavior:

- The payload is treated as plain string data
- No injected function executes
- No `INJECTEDbyMK` error appears in CloudWatch logs
- Normal valid requests continue to work

## Security Analysis

### Intended Security Rules

- User input must be treated strictly as data
- User input must never be executed as code
- Request fields must be validated before processing
- Dependencies must not introduce dynamic execution behavior on untrusted input

### Deviation

The vulnerable application executed attacker-controlled input during deserialization. This violates the rule that request data must not influence code execution.

**Deviation class:** intentional misuse / security-relevant abuse

### Behavior Comparison

| State | Behavior |
|---|---|
| Normal behavior | Valid request returns expected order data |
| Exploit behavior | Serialized function executes and throws `INJECTEDbyMK` |
| Post-fix behavior | Payload is not executed and the application continues safely |

## Lesson 9: Vulnerable Dependencies

This exploit is directly tied to dependency risk. The vulnerable `node-serialize` package allowed function reconstruction through the `_$$ND_FUNC$$_` / `$$ND_FUNC$$` pattern. When used on untrusted request input, that behavior led to arbitrary code execution.

The application also used `node-jose`, which has documented security concerns such as invalid curve attacks, regular expression denial of service, and risk from vulnerable transitive dependencies. These issues were not exploited in this lesson, but they increase the application's attack surface.

Secure dependency management should include:

- regular dependency vulnerability scanning
- replacing libraries that execute or evaluate untrusted input
- updating vulnerable packages where secure versions exist
- removing unused dependencies from deployed Lambda packages
- reviewing transitive dependencies, not only direct dependencies

## Takeaway

Unsafe deserialization is especially dangerous in serverless applications because successful exploitation gives the attacker code execution inside the Lambda environment. From there, the impact can extend to environment variables, internal services, and AWS resources available through the function execution role.

The core lesson is that request data must remain data. Do not deserialize, evaluate, or execute user-controlled content. Use safe parsers, validate input with allowlists, and remove dependencies that make code execution possible from untrusted input.

## Report Reference

The original report and screenshots remain in [`Lesson1andLesson9Report.docx`](Lesson1andLesson9Report.docx). That file was not modified.
