# Lesson 5: Broken Access Control

## Project Summary

This lesson demonstrates a Broken Access Control vulnerability in the DVSA application. The normal payment workflow should require a user to create an order, add shipping information, and complete billing before the order is marked as paid.

The vulnerability allowed an attacker to bypass the payment process by abusing unsafe handling of the `action` parameter. A crafted payload could invoke privileged backend functionality, including the admin-only `DVSA-ADMIN-UPDATE-ORDERS` function, and directly modify an order in DynamoDB.

## Learning Goals

- Demonstrate how unsafe input handling can lead to broken access control
- Show how a user-controlled `action` field can become a privileged execution path
- Verify unauthorized order modification through DynamoDB
- Remove unsafe deserialization from the central request handler
- Confirm that normal order and shipping functionality still works after the fix

## Repository Layout

```text
Lesson5/
|-- README.md
|-- Lesson5Report.docx
|-- Before Fix/
|   |-- Request1.png
|   |-- Request2.png
|   |-- Request3.png
|   `-- DynamoDB_ConfirmsVulnerabilityWorked.png
`-- After Fix/
    |-- Code Fix in DVSA-ORDER-MANAGER.png
    |-- Request1.png
    |-- Request2.png
    |-- Request3ShouldNotWork.png
    `-- UnchangedDynamoDB.png
```

## Vulnerability Summary

**Vulnerability:** Broken Access Control

**Related weaknesses:**

- Insecure deserialization
- Privilege escalation
- Unsafe dynamic backend dispatch

**Affected components:**

- API Gateway `/order` endpoint
- `DVSA-ORDER-MANAGER` Lambda function
- `DVSA-ADMIN-UPDATE-ORDERS` Lambda function
- DynamoDB order table

**Root cause:** The request handler used unsafe deserialization on user-controlled input and did not properly restrict access to privileged backend functions. Because `DVSA-ORDER-MANAGER` had permission to invoke internal Lambda functions, attacker-controlled input could be used to reach administrative functionality.

## Why This Works

The vulnerable system allowed user input to influence backend execution in three ways:

- the `action` field was trusted as part of backend dispatch logic
- user-controlled request bodies were unserialized using `node-serialize`
- the request-handling Lambda had permission to invoke internal admin Lambda functions

This created a privilege escalation path:

```text
user input -> code execution -> internal Lambda invocation -> DynamoDB order modification
```

As a result, an attacker could mark an order as paid without completing the billing process.

## Environment and Tools

The vulnerability was tested in an AWS-hosted DVSA environment.

Components:

- API Gateway endpoint for `/order`
- AWS Lambda order-processing functions
- DynamoDB order table
- Browser session with a valid authorization token

Tools used:

- Postman
- Browser Developer Tools
- AWS Console
- DynamoDB table view

## Reproducing the Vulnerability

### 1. Create a New Order

Send a standard order creation request using `action: new`.

Expected behavior:

- the API creates a valid order
- the response includes an `order-id`

Evidence:

- [`Before Fix/Request1.png`](<Before Fix/Request1.png>)

### 2. Add Shipping Information

Send a shipping request for the created order.

Expected behavior:

- the API updates the shipping address
- the order continues through the normal checkout flow

Evidence:

- [`Before Fix/Request2.png`](<Before Fix/Request2.png>)

### 3. Send the Exploit Request

Send a crafted request containing a malicious `action` payload designed to invoke hidden administrative functionality.

Observed API behavior:

- the API returned an `unknown action` response
- this response did not fully reflect what happened inside the backend

Evidence:

- [`Before Fix/Request3.png`](<Before Fix/Request3.png>)

### 4. Verify the Order in DynamoDB

Inspect the order record directly in DynamoDB.

Observed unauthorized changes:

- `orderStatus` updated to `120`
- `totalAmount` updated
- `confirmationToken` populated
- `paymentTS` set

Evidence:

- [`Before Fix/DynamoDB_ConfirmsVulnerabilityWorked.png`](<Before Fix/DynamoDB_ConfirmsVulnerabilityWorked.png>)

These changes confirm that the admin function executed and modified the order directly, bypassing the normal billing process.

## Evidence and Proof

The strongest proof is the DynamoDB state after the exploit request. Even though the API response showed `unknown action`, the order record changed to a paid state.

This confirms:

- normal order creation worked before exploitation
- shipping updates worked normally
- the crafted request reached privileged backend behavior
- the order was modified without completing billing

## Fix Strategy

The fix is to remove unsafe deserialization and enforce strict access control on privileged backend operations.

Required mitigations:

- replace `node-serialize` request parsing with safe JSON parsing
- treat all user input strictly as data
- validate allowed `action` values
- reject malformed request bodies
- require authorization before privileged operations
- prevent user-controlled input from invoking admin-only Lambda functions
- restrict Lambda invoke permissions according to least privilege

## Code and Configuration Changes

The vulnerable code in `DVSA-ORDER-MANAGER` was changed.

Original vulnerable code:

```javascript
var req = serialize.unserialize(event.body);
var headers = serialize.unserialize(event.headers);
```

Secure parsing logic:

```javascript
let req = {};
let headers = {};

try {
    req = typeof event.body === "string" ? JSON.parse(event.body) : event.body;
    headers = event.headers || {};
} catch (e) {
    const response = {
        statusCode: 400,
        headers: {
            "Access-Control-Allow-Origin" : "*"
        },
        body: JSON.stringify({"status": "err", "msg": "invalid request body"})
    };
    return callback(null, response);
}
```

Additional changes:

- removed the `node-serialize` dependency from request handling
- ensured only one `headers` variable is defined
- added validation for missing authorization headers
- prevented injected code from executing through the `action` field

Evidence:

- [`After Fix/Code Fix in DVSA-ORDER-MANAGER.png`](<After Fix/Code Fix in DVSA-ORDER-MANAGER.png>)

## Verification After Fix

### 1. Normal Functionality Test

A new order was created using the updated code, and shipping information was added successfully.

Evidence:

- [`After Fix/Request1.png`](<After Fix/Request1.png>)
- [`After Fix/Request2.png`](<After Fix/Request2.png>)

### 2. Exploit Replay Test

The previous `_$$ND_FUNC$$_` exploit payload was sent again with modified marker values.

Observed result:

- the API returned an error response
- the injected function did not execute
- privileged backend functionality was not invoked

Evidence:

- [`After Fix/Request3ShouldNotWork.png`](<After Fix/Request3ShouldNotWork.png>)

### 3. DynamoDB Verification

The corresponding order record was inspected after the replay test.

Observed result:

- `orderStatus` remained unchanged
- `confirmationToken` was not modified
- `totalAmount` was not altered

Evidence:

- [`After Fix/UnchangedDynamoDB.png`](<After Fix/UnchangedDynamoDB.png>)

This confirms that the exploit is no longer effective and arbitrary code execution through the `action` field has been blocked.

## Security Analysis

### Intended Security Rules

- Users must not be able to mark orders as paid without completing billing
- Administrative functions must not be reachable through public request parameters
- User input must never be executed as code
- Access control must be enforced before privileged operations
- Lambda invoke permissions must follow least privilege

### Behavior Trace

| State | Observed Behavior |
|---|---|
| Normal behavior | Order creation and shipping work through expected user actions |
| Exploit behavior | Crafted payload invokes admin update behavior and modifies DynamoDB |
| Post-fix behavior | Payload is rejected and the order remains unchanged |

### Deviation

The vulnerable behavior violates access-control rules because a normal user can reach admin-only functionality and modify payment-related order fields.

**Deviation class:** Broken Access Control / privilege escalation

## Structured Summary

| Vulnerability | Intended Rule | Artifacts Used | Normal Behavior Evidence | Exploit Behavior Evidence |
|---|---|---|---|---|
| Broken Access Control | Users must not bypass billing or invoke admin-only functions | Postman responses, DynamoDB records, Lambda request logic | Order creation and shipping work normally | Order marked paid in DynamoDB without billing |

| Vulnerability | Why This Is a Deviation | Deviation Class | Fix Applied | Post-Fix Verification |
|---|---|---|---|---|
| Broken Access Control | User-controlled input reached privileged backend functionality | Privilege escalation / security-relevant abuse | Removed unsafe deserialization and restricted admin invocation in `DVSA-ORDER-MANAGER` | Exploit payload rejected and DynamoDB order remains unchanged |

## Takeaway

This exercise shows how one unsafe coding practice can break multiple security boundaries. Deserializing user input as executable content allowed an attacker to move from a public API request into internal Lambda invocation and then into direct database modification.

Access control must be enforced at every layer, not only at the API surface. In serverless systems, Lambda permissions and internal function boundaries are part of the security model and must be designed with least privilege.

## Report Reference

The original report and screenshots remain in [`Lesson5Report.docx`](Lesson5Report.docx), [`Before Fix/`](<Before Fix/>), and [`After Fix/`](<After Fix/>). Those files were not modified.
