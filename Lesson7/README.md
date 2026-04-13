# Lesson 7: Over-Privileged Function

## Project Information

- Course: ICS344-03
- Students: Saad W. (202337730) and Mohamed K. (202338790)
- Target URL: `http://dvsa-website-project-238043187633-us-east-1.s3-website.us-east-1.amazonaws.com/cart`
- AWS Region: `us-east-1`
- Date: `2026-04-12`

## Lesson Summary

This lesson demonstrates an **Over-Privileged Function** vulnerability in the DVSA application. The issue affects the Lambda execution role used by the `DVSA-SEND-RECEIPT-EMAIL` function.

The role grants access to AWS resources that are not required for the function's intended behavior. Because Lambda code inherits the permissions of its execution role, any compromise of the function can be used to access unrelated resources such as S3 buckets and DynamoDB tables.

## Goal

The goal of this lesson is to show how excessive IAM permissions increase the blast radius of a compromised Lambda function and how least-privilege IAM policies reduce that risk.

## Root Cause

The vulnerability exists because the Lambda execution role was configured with permissions far broader than necessary.

Instead of allowing only the actions needed to send receipt emails, the role included:

- broad S3 permissions
- broad DynamoDB permissions
- unnecessary SES administrative privileges
- wildcard resource access

This violates the principle of least privilege. If the function is exploited, the attacker can use the inherited temporary credentials to perform actions across multiple AWS services.

## Environment and Tools

The testing environment used a deployed DVSA instance in AWS:

- Frontend hosted on an S3 website endpoint
- Backend exposed through API Gateway and AWS Lambda
- Target function: `DVSA-SEND-RECEIPT-EMAIL`

Tools used:

- AWS Management Console
- IAM Policy Simulator
- AWS CloudTrail
- CloudWatch Logs

## Reproduction Steps

### 1. Locate the Lambda Function

- Open the AWS Console
- Navigate to the `DVSA-SEND-RECEIPT-EMAIL` Lambda function
- Open the **Permissions** tab
- Follow the execution role link to inspect the attached IAM policies

### 2. Review the Attached Policies

Check the role for over-privileged policies. The report identified permissions such as:

- `AWSLambdaBasicExecutionRole`
- `AmazonSESFullAccess`
- S3 access using wildcard resources
- DynamoDB access using wildcard resources

These permissions indicate that the function can access more resources than it actually needs.

### 3. Validate Access with IAM Policy Simulator

Use IAM Policy Simulator to test the execution role against actions such as:

- `s3:GetObject`
- `s3:PutObject`
- `dynamodb:Scan`
- `dynamodb:GetItem`
- `dynamodb:PutItem`
- `dynamodb:DeleteItem`

Observed result:

- The simulator allows these actions
- The role can access S3 buckets and DynamoDB tables beyond the receipt workflow

### 4. Compare Allowed Permissions with Actual Use

- Enable or inspect CloudTrail for recent function activity
- Trigger the workflow by placing an order in DVSA
- Generate a policy from the observed access history

Observed behavior:

- The function only used a small set of permissions
- The report identified actual usage around:
  - CloudWatch Logs
  - KMS Decrypt
  - STS GetCallerIdentity

This confirms a mismatch between what the role allows and what the function really uses.

## Evidence and Proof

The vulnerability is supported by two main observations:

1. IAM Policy Simulator shows that the role is allowed to access S3 and DynamoDB resources broadly.
2. CloudTrail-based policy generation shows that the function only uses minimal permissions during normal execution.

This gap proves the role is over-privileged. The extra permissions are not needed for the function's intended behavior and increase the impact of compromise.

## Security Analysis

### Intended Security Rules

- Lambda execution roles must follow least privilege
- Functions should access only the resources required for their task
- Wildcard permissions should be avoided unless strictly necessary

### Normal Behavior

Under normal operation, the receipt function should only need permissions related to:

- logging
- limited identity checks
- any narrowly scoped receipt-email dependencies

### Risk Behavior

Because the execution role is too broad, an attacker who gains code execution in the function can attempt to:

- read or write unrelated S3 objects
- access unrelated DynamoDB tables
- use permissions outside the receipt workflow

### Deviation Classification

This case is classified as:

- intentional misuse / security-relevant abuse

The deviation comes from improper IAM role design, not from the function's intended business logic.

## Fix Strategy

The mitigation is to redesign the execution role according to least privilege.

Required changes:

- remove wildcard resource permissions
- limit S3 access to the DVSA receipts bucket only
- limit DynamoDB access to the exact DVSA tables required
- reduce SES permissions to only the send actions needed by the receipt workflow

## Configuration Changes

The report describes IAM policy changes rather than application code changes.

Main policy updates:

- removed wildcard permissions
- replaced broad S3 access with bucket-specific permissions
- replaced broad DynamoDB access with table-specific permissions
- reduced SES permissions to the minimum required actions

## Verification After Fix

After applying the least-privilege policy:

- the DVSA order workflow was tested again
- the receipt function still completed successfully
- access to unrelated S3 buckets and DynamoDB tables was no longer permitted

This confirms that the fix preserved functionality while reducing unnecessary privilege.

## Behavior Comparison

| State | Observed Behavior |
|---|---|
| Normal behavior | Function uses only minimal permissions such as logs, KMS, and identity-related actions |
| Vulnerable state | Role allows broad access to S3 and DynamoDB resources unrelated to the receipt workflow |
| Post-fix state | Function still works, but unnecessary access is removed |

## Takeaway

This lesson shows that IAM roles are a major security boundary in serverless systems. If a Lambda function is compromised, the attacker immediately gains the permissions of its execution role.

Over-privileged roles greatly increase attack impact. Applying least privilege limits the blast radius and helps keep serverless applications secure.

## Report Reference

The original report and screenshots remain in [`Lesson7Report.docx`](Lesson7Report.docx). That file was not modified.
