# DVSA Broken Authentication (JWT) Exploit and Fix

## Project Summary

This repository documents a Broken Authentication issue in the AWS DVSA (Damn Vulnerable Serverless Application). The vulnerable backend decodes JWTs but does not verify their signature before trusting the claims. Because of that, an attacker can modify the token payload, impersonate another user, and attempt to access that user's data.

The repository also includes a secure remediation approach using AWS Cognito JWKS-based signature verification.

## Learning Goals

- Understand how JWT-based authentication is supposed to work
- Demonstrate the risk of trusting decoded claims without signature verification
- Reproduce a user impersonation attempt with a forged token
- Show how to fix the issue by verifying Cognito-issued JWTs correctly

## Repository Layout

```text
Lesson2/
|-- README.md
|-- Lesson2Report.docx
|-- config/
|   `-- env.example.ps1
|-- scripts/
|   |-- decode.py
|   |-- forge.py
|   `-- get-orders.ps1
|-- fix/
|   |-- auth-snippet.js
|   |-- catch-snippet.js
|   |-- jwt-verification.js
|   `-- package.json
`-- evidence/
    `-- README.md
```

## Requirements

- AWS DVSA environment already deployed and reachable
- AWS CLI on Windows PowerShell
- Python 3
- Node.js 18+ if you want to test the fix helper code locally
- Two valid Cognito tokens captured from DVSA users

## Environment Setup

1. Install the AWS CLI if it is not already present.

```powershell
Invoke-WebRequest "https://awscli.amazonaws.com/AWSCLIV2.msi" -OutFile "AWSCLIV2.msi"
Start-Process msiexec.exe -Wait -ArgumentList '/i AWSCLIV2.msi'
aws --version
```

2. Copy the values from [`config/env.example.ps1`](config/env.example.ps1) into your current PowerShell session and replace the placeholders with your own values.

Important variables:

- `API_URL`: DVSA order endpoint
- `TOKEN_B`: a valid token for the attacker-controlled user
- `TOKEN_C`: a valid token for the victim user
- `VICTIM_USERNAME`: victim username claim
- `VICTIM_SUB`: victim subject claim

## Reproducing the Vulnerability

### 1. Capture Valid Tokens

- Open the DVSA application in a browser
- Sign in as two separate users
- In DevTools, inspect the network traffic
- Record the API endpoint and authorization tokens for User B and User C

### 2. Decode the Tokens

Use the helper script to inspect the JWT payloads:

```powershell
python scripts/decode.py
```

Expected result:

- `TOKEN_B` prints the attacker-controlled claims
- `TOKEN_C` prints the victim claims
- You confirm the victim `username` and `sub` values before forging a token

### 3. Verify Normal Behavior

Call the orders endpoint with the legitimate User B token:

```powershell
.\scripts\get-orders.ps1 -Token $env:TOKEN_B
```

Expected result:

- Only User B's records should be returned

### 4. Forge a JWT

Create a token that keeps User B's original header and signature but replaces the payload claims with User C's identity:

```powershell
$env:FAKE_AS_C = python scripts/forge.py
```

### 5. Attempt the Exploit

Send the forged token to the same endpoint:

```powershell
.\scripts\get-orders.ps1 -Token $env:FAKE_AS_C
```

Expected vulnerable behavior:

- The backend accepts the modified token, or
- The backend fails in a way that still shows it trusted the tampered claims before proper verification

## Vulnerability Details

**Type:** Broken Authentication / JWT validation failure

**Root Cause:**

- The application decodes JWTs
- The decoded claims are trusted directly
- The JWT signature is not verified against Cognito's public keys

**Impact:**

- User impersonation
- Unauthorized access to user-specific data
- Potential account takeover if authorization is based only on manipulated claims

## Fix

The fix snippets in [`fix/`](fix) show how to verify Cognito JWTs before using any identity fields.

### Fix Summary

1. Download the Cognito JWKS document
2. Build a keystore from the public keys
3. Verify the JWT signature against the keystore
4. Validate the issuer
5. Only then read `username`, `cognito:username`, or `sub`

### Fix Files

- [`fix/jwt-verification.js`](fix/jwt-verification.js): Cognito JWKS retrieval and JWT verification
- [`fix/auth-snippet.js`](fix/auth-snippet.js): secure authorization header handling
- [`fix/catch-snippet.js`](fix/catch-snippet.js): consistent invalid-token response handling
- [`fix/package.json`](fix/package.json): dependency declaration for `node-jose`

### Post-Fix Expected Behavior

- Forged tokens are rejected
- Only valid Cognito-signed JWTs are accepted
- Users can access only their own data

## Evidence

The screenshots for this assignment are preserved in [`Lesson2Report.docx`](Lesson2Report.docx). The report file was intentionally left untouched.

Additional notes about evidence placement are in [`evidence/README.md`](evidence/README.md).

## Beginner Replication Notes

- Start by loading the PowerShell variables from [`config/env.example.ps1`](config/env.example.ps1)
- Use [`scripts/decode.py`](scripts/decode.py) to confirm the real claims before forging anything
- Use [`scripts/get-orders.ps1`](scripts/get-orders.ps1) both before and after token forgery so the behavior change is easy to compare
- Apply the secure fix in the relevant DVSA Lambda handler before any database lookup or authorization check

## Key Takeaway

Breaking authentication is more severe than many input-handling bugs because once identity can be forged, the rest of the authorization model becomes untrustworthy. JWTs must be verified, not just decoded.
