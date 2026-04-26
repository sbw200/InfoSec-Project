# Lesson 8: Logic Vulnerability

## Project Summary

This lesson demonstrates a logic vulnerability in the DVSA application caused by improper request sequencing. The issue affects backend order-processing logic that handles billing and order updates through API Gateway and AWS Lambda.

The vulnerability allows an attacker to manipulate order contents during billing by sending out-of-order requests. The attacker can pay for a smaller quantity of items while the final order reflects a larger quantity.

## Learning Goals

- Demonstrate a race condition in the billing and order update workflow
- Show how stale order data can lead to inconsistent payment results
- Identify the Time-of-Check to Time-of-Use (TOCTOU) weakness
- Enforce order state validation during billing
- Verify that final receipts match billed amounts after the fix

## Repository Layout

```text
Lesson8/
|-- README.md
|-- Lesson8Report.docx
|-- evidence/
|   |-- billing-order-response.png
|   |-- receipt.png
|   `-- update-api.png
`-- fix/
    |-- order_billing.py
    `-- update_order.py
```

## Vulnerability Summary

**Vulnerability:** Logic Vulnerability / Race Condition / TOCTOU

**Affected components:**

- API Gateway `/order` route
- order update Lambda logic
- billing Lambda logic
- final receipt generation

**Root cause:** The backend did not enforce strict ordering or synchronization between billing and order update requests.

The billing operation read the order contents at one point in time, while an update request could modify the same order before the transaction was finalized. Because there was no locking, state validation, or atomic transaction boundary, the system processed both requests independently and produced an inconsistent final state.

## Why This Works

The exploit works because billing and update operations are not synchronized.

Example attack sequence:

```text
1. Create order with quantity = 1
2. Send billing request
3. Immediately send update request changing quantity = 3
4. Billing uses old quantity
5. Final order stores new quantity
```

This is a Time-of-Check to Time-of-Use issue. The system checks one version of the order for billing but later uses a different version when recording the final order state.

## Environment and Tools

The vulnerability was tested against a deployed DVSA environment in AWS.

Components:

- frontend hosted as an S3 static website
- API Gateway routing requests to Lambda
- Lambda functions responsible for order processing
- `/order` API route

Tools used:

- Browser Developer Tools
- Postman
- AWS CloudWatch

## Reproducing the Vulnerability

### 1. Create an Order with a Small Quantity

Create an order and set the quantity of an item to a small value, such as `1`.

Goal:

- ensure the billing request calculates a lower total amount

### 2. Send the Billing Request

Send a valid billing request using payment details captured from the normal workflow.

Evidence:

- [`evidence/billing-order-response.png`](evidence/billing-order-response.png)

### 3. Immediately Send an Update Request

Immediately after the billing request, send an update request that increases the same item quantity, such as changing the quantity from `1` to `3`.

Evidence:

- [`evidence/update-api.png`](evidence/update-api.png)

### 4. Review the Final Receipt

Check the final receipt after both requests complete.

Observed result:

- billing response showed a successful charge of `$33`
- final receipt showed quantity `3`
- final receipt total still showed `$33`

Evidence:

- [`evidence/receipt.png`](evidence/receipt.png)

## Evidence and Proof

The vulnerability is confirmed by the mismatch between the billed amount and final order contents.

Observed exploit result:

```text
Billed amount: $33
Final receipt quantity: 3
Final receipt total: $33
```

This proves that the system charged based on stale order data while storing the updated order state.

## Fix Strategy

The fix is to enforce synchronization between billing and update operations.

Required mitigations:

- introduce an order status such as `processing`
- set the order to `processing` when billing begins
- reject update requests while an order is in `processing` or completed state
- re-validate order contents immediately before charging
- use conditional writes or transactional updates for state changes
- process billing and final order updates as one consistent operation where possible

## Code and Configuration Changes

The backend Lambda logic should enforce strict state validation.

Before the fix:

- update requests could modify an order while billing was in progress
- billing could complete using stale order data
- receipt state could differ from charged state

After the fix:

- billing logic locks or marks the order as processing
- update logic checks the order status before applying changes
- updates are rejected during billing or after completion
- billing re-validates the order before charging

Fix files:

- [`fix/order_billing.py`](fix/order_billing.py)
- [`fix/update_order.py`](fix/update_order.py)

## Verification After Fix

After applying the fix, the same attack sequence was repeated:

1. create an order with a smaller quantity
2. send a billing request
3. immediately send an update request to increase the quantity

Post-fix expected behavior:

- the update request is rejected during billing, or
- the update is processed only after billing completes in a safe state
- the final receipt matches the billed amount
- inconsistent order state is prevented

## Security Analysis

### Intended Security Rules

- The system must prevent updates during billing
- The billed amount must match the final order contents
- Related order operations must be processed atomically or with strict state transitions
- The order state must remain stable while payment is being processed

### Behavior Trace

| State | Observed Behavior |
|---|---|
| Normal behavior | User updates the order, completes billing, and receipt matches billed amount |
| Exploit behavior | Billing charges for 1 item while final receipt shows 3 items |
| Post-fix behavior | Updates during billing are rejected and receipt matches billed amount |

### Deviation

The vulnerable behavior is a deviation from intended system logic because the system allows order modification during billing, causing payment and receipt state to diverge.

**Deviation class:** intentional misuse / security-relevant abuse

## Structured Summary

| Vulnerability | Intended Rule | Artifacts Used | Normal Behavior Evidence | Exploit Behavior Evidence |
|---|---|---|---|---|
| Logic Vulnerability / Race Condition / TOCTOU | Billing must reflect final order state and updates must not occur during billing | API requests, responses, receipt, request timing | Order quantity matches billed total | System charged for 1 item while receipt shows 3 items |

| Vulnerability | Why This Is a Deviation | Deviation Class | Fix Applied | Post-Fix Verification |
|---|---|---|---|---|
| Logic Vulnerability / Race Condition | System allows order modification during billing, creating inconsistent state | Intentional misuse / security-relevant abuse | Backend Lambda billing and update logic using conditional expressions and state locking | Update requests rejected during billing and receipt matches billed amount |

## Takeaway

This lesson shows that authentication and input validation are not enough when application workflows depend on correct sequencing. Race conditions can let attackers manipulate business logic without bypassing traditional controls.

Critical workflows such as billing require atomic operations, strict state transitions, and validation at the moment of use. The system must ensure that the data used for charging is the same data represented in the final order and receipt.

## Report Reference

The original report and screenshots remain in [`Lesson8Report.docx`](Lesson8Report.docx), [`evidence/`](evidence/), and [`fix/`](fix/). Those files were not modified.
