# S3 Live Upload Verification

Date: 2026-09-18

## Scope

Verified the production S3 upload path using the personal AWS development
account and the `personal` AWS CLI profile.

No credentials, AWS account identifiers, IAM usernames, ETags, or S3 version
identifiers are recorded in this document.

## Commands

```powershell
make db-up
make db-migrate
make run SYMBOL=AAPL