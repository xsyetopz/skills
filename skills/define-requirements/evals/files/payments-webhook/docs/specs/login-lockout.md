# Login lockout

## Requirements

- REQ-LCK-001 [source: issue 77] When a user enters a wrong password five
  times within one lockout window, the auth service shall lock the account
  for the rest of that window.
- REQ-LCK-002 [source: issue 77] While an account is locked, the auth
  service shall reject every login attempt with the error `account_locked`.

## Acceptance criteria

- AC-LCK-001 verifies REQ-LCK-001: Given an account with four failed
  attempts in the current window, when a fifth wrong password is entered,
  then the account is locked.
- AC-LCK-002 verifies REQ-LCK-002: Given a locked account, when the correct
  password is entered, then the response is `account_locked`.

## Open decisions

- DEC-LCK-001: Length of the lockout window.
