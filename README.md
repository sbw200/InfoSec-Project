# DVSA Serverless Security Lessons

## Project Summary

This repository documents a set of security lessons performed against the Damn Vulnerable Serverless Application (DVSA) deployed in AWS. The work focuses on common serverless security failures across API Gateway, AWS Lambda, Amazon S3, DynamoDB, IAM, Cognito JWT handling, and dependency management.

Each lesson folder contains a focused README, the original report document, evidence screenshots or artifacts, and any fix snippets or configuration examples used for mitigation.

## Repository Layout

```text
InfoSec Project/
|-- README.md
|-- Project Report.docx
|-- Project Report.pdf
|-- Lesson1 and Lesson9/
|-- Lesson2/
|-- Lesson3/
|-- Lesson4/
|-- Lesson5/
|-- Lesson6/
|-- Lesson7/
|-- Lesson8/
`-- Lesson10/
```

## Lessons Overview

| Lesson | Vulnerability | Main Risk | README |
|---|---|---|---|
| Lesson 1 and 9 | Event Injection and Vulnerable Dependencies | Unsafe deserialization with `node-serialize` allows attacker-controlled code execution, and vulnerable dependencies increase systemic risk | [Lesson1 and Lesson9/README.md](<Lesson1 and Lesson9/README.md>) |
| Lesson 2 | Broken Authentication | JWTs are decoded but not properly verified, allowing forged claims and user impersonation attempts | [Lesson2/README.md](Lesson2/README.md) |
| Lesson 3 | Sensitive Information Disclosure | Weak access control around receipt-generation logic can expose S3-hosted receipt data through presigned URLs | [Lesson3/README.md](Lesson3/README.md) |
| Lesson 4 | Insecure Cloud Configuration | Overly permissive S3 write access allows unauthorized uploads that trigger backend processing | [Lesson4/README.md](Lesson4/README.md) |
| Lesson 5 | Broken Access Control | Unsafe request handling allows admin-only order update functionality to be invoked and payment workflow bypassed | [Lesson5/README.md](Lesson5/README.md) |
| Lesson 6 | Denial of Service | Lack of request throttling lets concurrent billing requests exhaust Lambda capacity | [Lesson6/README.md](Lesson6/README.md) |
| Lesson 7 | Over-Privileged Function | Lambda execution role grants broader S3, DynamoDB, and SES permissions than required | [Lesson7/README.md](Lesson7/README.md) |
| Lesson 8 | Logic Vulnerability / Race Condition | Out-of-order billing and update requests create a TOCTOU issue where final order state does not match billed amount | [Lesson8/README.md](Lesson8/README.md) |
| Lesson 10 | Information Disclosure | Raw Lambda exceptions expose stack traces, file paths, function names, and line numbers | [Lesson10/README.md](Lesson10/README.md) |

## Common Environment

The lessons were tested against a deployed DVSA environment in AWS.

Common components:

- Amazon S3 static website frontend
- Amazon API Gateway
- AWS Lambda backend functions
- DynamoDB order storage
- Amazon S3 receipt storage
- AWS Cognito/JWT authentication paths
- CloudWatch Logs for backend evidence

Common tools:

- Browser Developer Tools
- Postman
- AWS Console
- AWS CLI
- CloudWatch Logs
- DynamoDB table inspection
- Python and PowerShell helper scripts where needed

## High-Level Findings

The lessons show that serverless security depends on several layers working together:

- request data must be parsed safely and never executed
- authentication tokens must be verified, not only decoded
- privileged Lambda functions must not be reachable from public request paths
- S3 buckets and IAM roles must follow least privilege
- critical workflows such as billing need state consistency and request sequencing
- API Gateway and Lambda need throttling and concurrency controls
- backend errors must be sanitized before being returned to users
- third-party dependencies must be reviewed and replaced when unsafe

## Fix Themes

Across the lessons, the major mitigation patterns were:

- replacing unsafe deserialization with `JSON.parse` or safe JSON parsing
- validating request fields against expected actions and formats
- verifying Cognito JWT signatures before trusting claims
- restricting administrative function invocation
- applying S3 bucket policies to block unauthorized writes
- reducing IAM permissions to least privilege
- adding API Gateway throttling and Lambda concurrency controls
- using state locks or conditional updates for billing workflows
- wrapping Lambda logic in exception handling and returning generic errors
- scanning and removing vulnerable dependencies

## Reports and Evidence

The root project reports are:

- [Project Report.docx](<Project Report.docx>)
- [Project Report.pdf](<Project Report.pdf>)

Each lesson folder also keeps its own report and evidence artifacts. The README files are intended as quick technical summaries; the `.docx` reports preserve the original screenshots and assignment writeups.

## Lesson Index

- [Lesson 1 and Lesson 9: Event Injection and Vulnerable Dependencies](<Lesson1 and Lesson9/README.md>)
- [Lesson 2: Broken Authentication](Lesson2/README.md)
- [Lesson 3: Sensitive Information Disclosure](Lesson3/README.md)
- [Lesson 4: Insecure Cloud Configuration](Lesson4/README.md)
- [Lesson 5: Broken Access Control](Lesson5/README.md)
- [Lesson 6: Denial of Service](Lesson6/README.md)
- [Lesson 7: Over-Privileged Function](Lesson7/README.md)
- [Lesson 8: Logic Vulnerability](Lesson8/README.md)
- [Lesson 10: Information Disclosure Through Improper Error Handling](Lesson10/README.md)

## Key Takeaway

The DVSA lessons demonstrate that serverless applications are secured through the combined behavior of application code, dependencies, cloud configuration, IAM permissions, API controls, and workflow design. A weakness in any one layer can expose backend systems, sensitive data, or critical business logic.
