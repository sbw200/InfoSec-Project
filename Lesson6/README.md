# Lesson 6: Denial of Service

## Project Summary

This lesson demonstrates a Denial of Service (DoS) vulnerability in the DVSA application. The issue affects the billing workflow handled through API Gateway and AWS Lambda.

The vulnerability allowed an attacker to send multiple concurrent billing requests and consume the available backend processing capacity. Once Lambda concurrency was exhausted, legitimate users could experience delays, errors, or service unavailability while attempting billing operations.

## Learning Goals

- Demonstrate how uncontrolled concurrent requests can exhaust serverless resources
- Show how billing functionality can become unavailable under abusive traffic
- Identify Lambda throttling evidence in CloudWatch logs
- Apply API Gateway throttling and Lambda concurrency controls
- Verify that excessive requests are limited after the fix

## Repository Layout

```text
Lesson6/
|-- README.md
|-- Lesson6Report.docx
|-- scripts/
|   `-- DOSAttack.py
|-- evidence/
|   |-- postman.png
|   |-- DOSattack.png
|   `-- cloudwatch-too-manyrequests.png
`-- fix/
    `-- image.png
```

## Vulnerability Summary

**Vulnerability:** Denial of Service

**Affected components:**

- API Gateway `/order` route
- billing action in the order workflow
- AWS Lambda billing backend
- Lambda concurrency capacity

**Root cause:** Weak resource protection and lack of effective request throttling.

The billing system relied on AWS Lambda functions with limited concurrent execution capacity. Because the API did not enforce effective rate limiting, per-user throttling, or request prioritization, an attacker could send a burst of parallel billing requests and occupy available Lambda execution slots.

## Why This Works

AWS Lambda has concurrency limits. When those limits are reached, additional invocations are throttled. In the vulnerable configuration, the application did not prevent a single actor from generating enough parallel billing requests to consume shared backend capacity.

The original API Gateway throttling configuration allowed very high traffic:

```text
Rate = 10000
Burst = 5000
```

With limits this high, abusive request bursts could reach the Lambda backend and trigger concurrency exhaustion before the API layer meaningfully protected the service.

## Environment and Tools

The vulnerability was tested against a DVSA deployment in AWS.

Components:

- AWS Region: `us-east-1`
- Frontend hosted as an S3 static website
- API Gateway routing requests to Lambda
- Lambda billing workflow behind the `/order` route

Tools used:

- Postman
- Python concurrent request script
- AWS CloudWatch Logs

## Reproducing the Vulnerability

### 1. Verify a Normal Billing Request

First, a normal billing request was sent to confirm that billing worked under standard conditions.

Evidence:

- [`evidence/postman.png`](evidence/postman.png)

### 2. Run the Concurrent Request Script

A Python script generated multiple concurrent requests targeting the billing endpoint.

Script:

- [`scripts/DOSAttack.py`](scripts/DOSAttack.py)

Observed behavior during the burst:

- degraded response reliability
- internal server errors
- bad gateway errors
- throttling once backend capacity was exhausted

Evidence:

- [`evidence/DOSattack.png`](evidence/DOSattack.png)

### 3. Inspect CloudWatch Logs

CloudWatch logs showed throttling and concurrency-limit failures.

Critical log evidence:

```text
errorType: TooManyRequestsException
httpStatusCode: 429
errorMessage: Rate Exceeded
Reason: ConcurrentInvocationLimitExceeded
```

Evidence:

- [`evidence/cloudwatch-too-manyrequests.png`](evidence/cloudwatch-too-manyrequests.png)

## Evidence and Proof

The vulnerability is confirmed by API responses and CloudWatch logs.

During concurrent execution, the system produced:

- `500 Internal Server Error`
- `502 Bad Gateway`
- `429 TooManyRequestsException`
- `ConcurrentInvocationLimitExceeded`

The `ConcurrentInvocationLimitExceeded` error confirms that the denial-of-service condition was caused by backend resource exhaustion in the Lambda environment.

## Fix Strategy

The fix is to introduce request-level resource protection so abusive traffic is controlled before it exhausts backend capacity.

Required mitigations:

- apply API Gateway rate limiting
- apply API Gateway burst limits
- add per-user throttling where possible
- use Lambda reserved concurrency for critical functions
- isolate billing capacity from less critical workflows
- consider queue-based processing or request buffering for burst handling
- detect and reject abnormal request patterns

## Code and Configuration Changes

The fix was implemented at the API Gateway and Lambda configuration levels.

Configuration before fix:

```text
Rate = 10000
Burst = 5000
```

Configuration after fix:

```text
Rate = 5
Burst = 10
```

Additional changes:

- adjusted Lambda concurrency controls
- improved fair distribution of execution capacity
- added validation logic to detect abnormal request patterns

Evidence:

- [`fix/image.png`](fix/image.png)

## Verification After Fix

After applying throttling and concurrency controls, the same concurrent request test was executed again.

Post-fix behavior:

- excessive requests were throttled at the API layer
- the backend no longer became unstable under load
- legitimate billing requests continued to work
- the denial-of-service condition was mitigated

## Security Analysis

### Intended Security Rules

- Billing functionality must remain available under normal and moderate load
- No single user should be able to consume all processing resources
- Critical billing operations must remain accessible to legitimate users
- Infrastructure limits must be protected by request-level controls

### Behavior Trace

| State | Observed Behavior |
|---|---|
| Normal behavior | A single billing request succeeds |
| Exploit behavior | Concurrent requests cause server errors and Lambda throttling |
| Post-fix behavior | Excessive requests are throttled and normal requests continue |

### Deviation

The vulnerable behavior deviates from intended system design because one actor can exhaust backend resources and degrade service availability for legitimate users.

**Deviation class:** intentional misuse / resource exhaustion attack

## Structured Summary

| Vulnerability | Intended Rule | Artifacts Used | Normal Behavior Evidence | Exploit Behavior Evidence |
|---|---|---|---|---|
| Denial of Service | Billing service must remain available and resistant to abuse | API responses, CloudWatch logs, script output | Single billing request succeeds normally | Concurrent requests cause `429` errors and service instability |

| Vulnerability | Why This Is a Deviation | Deviation Class | Fix Applied | Post-Fix Verification |
|---|---|---|---|---|
| Denial of Service | System allows resource exhaustion through uncontrolled parallel requests | Intentional misuse / resource exhaustion | API Gateway throttling and Lambda concurrency controls | Excessive requests are throttled and normal requests succeed |

## Takeaway

This lesson shows that availability is a core part of application security. Lambda concurrency limits protect infrastructure, but they do not automatically protect users from abusive request patterns.

Serverless applications need rate limiting, fair usage controls, and isolation for critical workflows. Security should be enforced at the API and application design levels so one actor cannot consume shared backend capacity and disrupt legitimate users.

## Report Reference

The original report and screenshots remain in [`Lesson6Report.docx`](Lesson6Report.docx), [`evidence/`](evidence/), [`scripts/`](scripts/), and [`fix/`](fix/). Those files were not modified.
