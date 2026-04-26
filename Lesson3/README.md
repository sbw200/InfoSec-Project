# Lesson 3: Sensitive Information Disclosure

## Project Summary

This lesson demonstrates a Sensitive Information Disclosure vulnerability in the DVSA application. The issue is caused by weak access control around administrative receipt-generation functionality in the backend.

The affected backend path involves AWS Lambda functions that can generate receipt download links for files stored in Amazon S3. By combining this weak access-control design with the previously identified Event Injection vulnerability, an attacker can attempt to reach privileged receipt-generation logic from an untrusted request path.

## Learning Goals

- Demonstrate how sensitive S3-hosted data can be exposed through backend functionality
- Show how unsafe input handling can create a path toward privileged Lambda functions
- Analyze the risk of presigned S3 URLs when authorization is weak
- Enforce separation between public request handling and administrative operations
- Verify that injected payloads no longer execute after the fix

## Repository Layout

```text
Lesson3/
|-- README.md
|-- Lesson3_Report.docx
|-- Postman.png
`-- evidence/
    |-- 2026-04-dvsa-order-receipts.zip
    `-- tmp/
        `-- 2026/
            `-- 04/
                `-- 14/
                    `-- 5dcb463d-71e5-4d0d-a027-cfdf1a34f300_54080488-5081-709d-d7a6-99052e8c6894.txt
```

## Vulnerability Summary

**Vulnerability:** Sensitive Information Disclosure

**Affected components:**

- `DVSA-ORDER-MANAGER`
- `DVSA-ADMIN-GET-RECEIPT`
- S3 receipt storage

**Root cause:** Unsafe input handling and improper access control over privileged backend operations.

The application processed user input with unsafe deserialization through `node-serialize`. This allowed attacker-controlled input to be interpreted as executable code instead of plain data. At the same time, the backend included an administrative function named `DVSA-ADMIN-GET-RECEIPT`, which could collect receipt files from S3, compress them into a zip archive, upload the archive back to S3, and generate a presigned download URL.

If an attacker could invoke that administrative function from a public request path, the generated `download_url` could expose receipt files belonging to other users.

## Environment and Tools

The vulnerability was tested against a deployed DVSA environment in AWS:

- AWS Region: `us-east-1`
- Frontend hosted as an S3 static website
- API exposed through Amazon API Gateway
- Backend implemented with AWS Lambda functions
- Primary API route tested: `/order`
- Main request handler: `DVSA-ORDER-MANAGER`
- Target privileged function: `DVSA-ADMIN-GET-RECEIPT`

Tools used:

- Postman
- AWS CloudWatch Logs
- Backend Lambda source-code review

## Reproducing the Vulnerability

### 1. Identify Unsafe Input Handling

The first step is confirming that the backend request handler processes user-controlled input through unsafe deserialization. This creates the possibility that attacker-supplied payloads can execute inside the Lambda function.

### 2. Craft an Admin Receipt Payload

A payload was crafted to attempt invocation of the privileged `DVSA-ADMIN-GET-RECEIPT` function. The payload included receipt-generation parameters such as year and month.

Goal of the payload:

- reach administrative receipt logic
- generate a receipt archive
- obtain a presigned S3 `download_url`

### 3. Send the Payload Through the Public API

The payload was sent to the `/order` API endpoint using Postman.

Observed behavior:

- the API returned either a `502 Internal Server Error`, or
- the API returned an `unknown action` response

### 4. Review CloudWatch Logs

CloudWatch logs were inspected to determine whether backend execution was reached.

The logs showed stack traces involving `node-serialize` and `eval`, confirming that injected payloads were executed by the Lambda runtime.

## Evidence and Proof

The vulnerability is supported by backend execution evidence and source-code analysis:

- CloudWatch logs show that attacker-controlled payloads reached executable backend paths
- stack traces reference `node-serialize` and `eval`
- the administrative function `DVSA-ADMIN-GET-RECEIPT` contains logic that generates a presigned S3 `download_url`
- the receipt archive evidence is stored in [`evidence/2026-04-dvsa-order-receipts.zip`](evidence/2026-04-dvsa-order-receipts.zip)
- Postman testing evidence is stored in [`Postman.png`](Postman.png)

The exploit did not fully retrieve sensitive data in this deployment because runtime behavior and missing dependencies prevented complete execution. However, the exposure path exists in principle: privileged receipt-generation functionality can expose sensitive S3 files if reached without proper authorization.

## Fix Strategy

The fix is to enforce strict separation between public API input and privileged administrative functionality.

Required mitigations:

- remove unsafe deserialization from `DVSA-ORDER-MANAGER`
- parse request bodies as safe JSON
- validate request fields against expected actions and formats
- prevent dynamic execution paths from user-controlled input
- require explicit authorization before invoking administrative functions
- generate presigned receipt URLs only after authorization succeeds
- keep administrative Lambda functions unreachable from public request paths unless access checks pass

## Code and Configuration Changes

The fix was applied in `DVSA-ORDER-MANAGER`.

Main changes:

- removed unsafe `node-serialize` request handling
- replaced unsafe deserialization with safe JSON parsing
- added validation so only expected request fields are processed
- restricted administrative function invocation so public inputs cannot directly trigger privileged receipt-generation logic

## Verification After Fix

After the fix, the same payload was tested again.

Post-fix expected behavior:

- attacker-controlled input is not executed
- the API rejects invalid input safely
- CloudWatch logs no longer show injected payload execution
- administrative receipt functionality is not reachable from the public request path
- normal API requests continue to work correctly

## Security Analysis

### Intended Security Rules

- User input must not be executed as code
- Administrative functionality must require proper authorization
- Sensitive receipt data must not be exposed through public endpoints
- Presigned URLs must only be generated for authorized users

### Behavior Trace

| State | Observed Behavior |
|---|---|
| Normal behavior | Valid requests return expected user-specific data |
| Exploit behavior | Injected payload triggers backend execution toward admin functionality |
| Post-fix behavior | Injected payloads are rejected and no execution occurs |

### Deviation

The vulnerable behavior is a deviation from intended design because user-controlled input can reach execution paths and attempt access to privileged receipt-generation logic.

**Deviation class:** intentional misuse / security-relevant abuse

## Structured Summary

| Vulnerability | Intended Rule | Artifacts Used | Normal Behavior Evidence | Exploit Behavior Evidence |
|---|---|---|---|---|
| Sensitive Information Disclosure | Administrative receipt data must not be accessible without authorization | CloudWatch logs, Lambda source code, API responses | Normal requests return only user-specific data | Injected payload triggers backend execution attempt toward admin functionality |

| Vulnerability | Why This Is a Deviation | Deviation Class | Fix Applied | Post-Fix Verification |
|---|---|---|---|---|
| Sensitive Information Disclosure | The system allows a path to privileged receipt-generation logic without proper access control | Intentional misuse / security-relevant abuse | Removed unsafe deserialization and restricted admin functionality in `DVSA-ORDER-MANAGER` | Payload execution is blocked and admin functionality is no longer reachable |

## Takeaway

This lesson shows that sensitive information disclosure can result from a chain of weaknesses, not only from a single exposed file or public bucket. Unsafe input handling made it possible to attempt backend execution, while weak authorization boundaries made privileged receipt-generation logic a meaningful target.

Even though the exploit did not fully succeed in this deployment, the design risk remains important. Security must be enforced through validation, authorization, and isolation of administrative operations rather than relying on runtime limitations or accidental execution failures.

## Report Reference

The original report and screenshots remain in [`Lesson3_Report.docx`](Lesson3_Report.docx). That file was not modified.
