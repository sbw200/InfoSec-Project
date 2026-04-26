# Lesson 4: Insecure Cloud Configuration

## Project Summary

This lesson demonstrates an Insecure Cloud Configuration vulnerability in the DVSA application. The application uses an Amazon S3 bucket to store order receipts, and backend Lambda functions process objects uploaded to that bucket.

The vulnerability existed because the S3 bucket allowed unauthorized users to upload files. Those uploads triggered backend receipt-processing logic without proper validation, allowing an attacker to influence backend execution through malformed or malicious object keys.

## Learning Goals

- Demonstrate how overly permissive S3 permissions can expose backend systems
- Show how unauthorized S3 uploads can trigger Lambda processing
- Identify the risk of trusting object key structure without validation
- Apply least-privilege access control to an S3 bucket
- Verify that unauthorized uploads are blocked after the fix

## Repository Layout

```text
Lesson4/
|-- README.md
|-- Lesson4Report.docx
`-- Screenshots/
    |-- Upload RAW File to S3.png
    |-- File Uploaded to S3 Proof.png
    |-- File Upload Breaks AWS Error.png
    |-- Updated Bucket Policy.png
    `-- Unauthorized Upload Denied.png
```

## Vulnerability Summary

**Vulnerability:** Insecure Cloud Configuration

**Affected components:**

- Amazon S3 receipt storage bucket
- `DVSA-SEND-RECEIPT-EMAIL` Lambda function
- CloudWatch logging for receipt processing

**Root cause:** Overly permissive S3 write access and insufficient validation of uploaded object keys.

The S3 receipts bucket accepted uploads from unauthorized users. Because those uploads triggered backend processing, attacker-controlled object keys became input to the Lambda function. The backend assumed uploaded files followed the expected receipt path and filename format, but malformed filenames caused runtime errors.

## Environment and Tools

The vulnerability was tested against a DVSA deployment in AWS.

Components:

- Amazon S3 receipt bucket: `dvsa-receipts-bucket-562825150177-us-east-1`
- AWS Lambda receipt-processing function: `DVSA-SEND-RECEIPT-EMAIL`
- Amazon API Gateway
- DynamoDB order data storage

Tools used:

- AWS CLI
- AWS Console for S3, Lambda, and CloudWatch
- CloudWatch Logs
- Windows command prompt

## Reproducing the Vulnerability

### 1. Identify the Receipt Bucket

The target receipt bucket was:

```text
dvsa-receipts-bucket-562825150177-us-east-1
```

### 2. Create a Local Test File

Create a small local file:

```powershell
echo test > empty.txt
```

### 3. Upload a File to S3

Use the AWS CLI to upload the file into the receipt bucket:

```powershell
aws s3 cp empty.txt s3://dvsa-receipts-bucket-562825150177-us-east-1/2026/04/23/test.raw
```

Evidence:

- [`Screenshots/Upload RAW File to S3.png`](<Screenshots/Upload RAW File to S3.png>)
- [`Screenshots/File Uploaded to S3 Proof.png`](<Screenshots/File Uploaded to S3 Proof.png>)

### 4. Confirm Backend Processing

After the upload, CloudWatch logs showed that the `DVSA-SEND-RECEIPT-EMAIL` Lambda function was triggered by the S3 event.

### 5. Upload a Malformed Filename

Upload another object with a malformed or unexpected filename:

```powershell
aws s3 cp empty.txt s3://dvsa-receipts-bucket-562825150177-us-east-1/2026/04/23/badfile.raw
```

Observed result:

- CloudWatch showed a backend error
- The reported error was `IndexError: list index out of range`

Evidence:

- [`Screenshots/File Upload Breaks AWS Error.png`](<Screenshots/File Upload Breaks AWS Error.png>)

## Evidence and Proof

The vulnerability is confirmed by three observations:

1. The S3 bucket accepted uploads from an unauthorized source.
2. Uploaded files appeared in the receipt bucket.
3. Uploaded object keys triggered backend Lambda processing and malformed names caused runtime errors.

This proves that external users could write to a sensitive S3 bucket and influence backend processing through object-key input.

## Fix Strategy

The primary mitigation is to enforce strict access control on the S3 bucket. The bucket must only allow writes from authorized AWS principals, such as the receipt-processing Lambda role or other explicitly approved application roles.

Defense-in-depth recommendations:

- validate object key structure before processing
- reject unexpected filename formats
- avoid assuming S3 event input is trusted
- limit Lambda triggers to trusted upload paths where possible
- log and safely ignore invalid objects instead of throwing runtime errors

## Code and Configuration Changes

The applied fix was an S3 bucket policy update.

The policy was modified to restrict write access so unauthorized users could no longer upload files to the receipt bucket. Only the intended receipt-processing role was allowed to write objects.

Evidence:

- [`Screenshots/Updated Bucket Policy.png`](<Screenshots/Updated Bucket Policy.png>)

Input validation in the Lambda function is recommended as an additional control, but it was not implemented as part of this exercise.

## Verification After Fix

After applying the bucket policy, the same AWS CLI upload command was tested again.

Observed result:

- S3 returned `AccessDenied`
- the unauthorized upload was blocked
- the backend Lambda function was not triggered by the external upload attempt

Evidence:

- [`Screenshots/Unauthorized Upload Denied.png`](<Screenshots/Unauthorized Upload Denied.png>)

Post-fix confirmation:

- unauthorized access to the S3 bucket is prevented
- backend receipt processing cannot be triggered by unauthorized users
- the vulnerability is mitigated through configuration changes

## Security Analysis

### Intended Security Rules

- Only authorized services should write to the receipt S3 bucket
- Backend systems must validate all external input
- S3 object keys must not be trusted without validation
- Cloud resources must follow least privilege

### Behavior Trace

| State | Observed Behavior |
|---|---|
| Normal behavior | Authorized uploads are processed successfully |
| Exploit behavior | Unauthorized uploads are accepted and trigger backend errors |
| Post-fix behavior | Unauthorized uploads are blocked with `AccessDenied` |

### Deviation

The vulnerable behavior is a deviation from the intended cloud security model because untrusted users could write to S3 and influence backend Lambda execution.

**Deviation class:** Insecure Cloud Configuration + Improper Input Validation

## Structured Summary

| Vulnerability | Intended Rule | Artifacts Used | Normal Behavior Evidence | Exploit Behavior Evidence |
|---|---|---|---|---|
| Insecure Cloud Configuration | Only authorized entities should write to S3 | S3 uploads, CloudWatch logs, AWS CLI output | Valid uploads processed successfully | Unauthorized uploads accepted and triggered backend processing |

| Vulnerability | Why This Is a Deviation | Deviation Class | Fix Applied | Post-Fix Verification |
|---|---|---|---|---|
| Insecure Cloud Configuration | Untrusted users can write to S3 and influence backend execution | Security-relevant misuse | S3 bucket policy update | `AccessDenied` returned and no backend execution occurred |

## Takeaway

This lesson demonstrates that cloud misconfiguration can introduce serious vulnerabilities even when the application code appears secure. S3 permissions must follow least privilege, and backend systems must treat object keys and event data as untrusted input.

Secure cloud configuration is part of the application security boundary. Preventing unauthorized writes to S3 protects both the data layer and the backend processing systems connected to it.

## Report Reference

The original report and screenshots remain in [`Lesson4Report.docx`](Lesson4Report.docx) and [`Screenshots/`](Screenshots/). Those files were not modified.
