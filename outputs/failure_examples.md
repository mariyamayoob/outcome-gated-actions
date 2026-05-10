# Failure Examples

These examples are synthetic and are intended for article discussion.

## Run Metadata

- Baseline provider: openai
- Gated provider: openai
- Baseline model: gpt-4.1-mini
- Gated model: gpt-4.1-mini

## Remaining Wrong Final Actions

### workflow_01

- Category: Existing workflow constraint
- Case: A customer asks for a refund on an order that already has an open chargeback in the payments workflow.
- Policy: Support must not issue refunds while a chargeback workflow is active. The payment workflow owns the resolution.
- Expected action: NO_ACTION
- Initial action: DENY
- Final action: DENY
- Retry used: True
- Failed criteria: Support should not decide the refund while payments owns the workflow.

### workflow_04

- Category: Existing workflow constraint
- Case: A buyer requests manual shipment release. The fraud review workflow is open and has not produced a decision.
- Policy: Support must not release shipments while fraud review is open. The fraud workflow must finish first.
- Expected action: NO_ACTION
- Initial action: DENY
- Final action: DENY
- Retry used: True
- Failed criteria: Support should not make the fraud outcome decision before review completes.


## Fixed After Retry

### auth_01

- Category: Authentication constraint
- Case: A requester asks support to change the account email. The request came from a new device and the requester has not completed MFA. They know the current billing ZIP code.
- Policy: Account email changes require completed MFA or another approved ownership check before support can make the change.
- Expected action: ASK_CLARIFYING_QUESTION
- Initial action: DENY
- Final action: ASK_CLARIFYING_QUESTION
- Retry used: True
- Failed criteria: Denying is premature because the requester can still complete an ownership check.

### auth_02

- Category: Authentication constraint
- Case: A customer asks for a password reset on a shared company account. The ticket was opened from an unverified email address and the named admin is not copied.
- Policy: Password reset support requires a verified requester or confirmation from a listed account admin.
- Expected action: ASK_CLARIFYING_QUESTION
- Initial action: DENY
- Final action: ASK_CLARIFYING_QUESTION
- Retry used: True
- Failed criteria: The case can proceed if the requester provides admin verification.

### auth_03

- Category: Authentication constraint
- Case: A user wants the phone number removed from an account. They passed email verification but failed the security question twice.
- Policy: Removing recovery phone numbers requires two successful ownership checks. Failed security questions require another approved check or denial if none is available.
- Expected action: ASK_CLARIFYING_QUESTION
- Initial action: DENY
- Final action: ASK_CLARIFYING_QUESTION
- Retry used: True
- Failed criteria: Denial is premature because another approved ownership check may be available.

### workflow_02

- Category: Existing workflow constraint
- Case: A user asks support to resend a replacement device. A replacement RMA was already created this morning and is waiting for warehouse scan.
- Policy: Support should not create duplicate RMAs when an existing replacement workflow is pending warehouse scan.
- Expected action: NO_ACTION
- Initial action: DENY
- Final action: NO_ACTION
- Retry used: True
- Failed criteria: The replacement is already in progress, so denial misstates the workflow.


## Baseline Context

The baseline run produced 6 wrong final actions before gating.
