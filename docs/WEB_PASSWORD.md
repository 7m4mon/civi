# Change the CIVI Web password

Open `/network#web-password` and use **Change Web password**:

1. Enter the current CIVI Web password. After LAN RESET this is the locally displayed recovery password, unless subsequently changed here.
2. Enter the new password twice (12–256 characters, no control characters).
3. Click **Change password**.

The change is immediate and persists across manual application restarts. Other pages and clients must use the new password. Neither CIVI nor the LAN helper needs restarting when a password is changed. The username remains `admin`.

Saved Web credentials override the startup password environment variable. The Pi `start.sh` launcher recognizes saved credentials and does not ask for an environment password. LAN RESET returns authentication to the device's recovery default; the user can then set a new custom password through this form again.

The credential file `.civi-web-auth.json` contains a random salt and PBKDF2-SHA256 hash (600,000 iterations), not the new plaintext password. On Linux it is atomically written with mode 600 and checked for ownership/permissions on load. It is excluded from Git. LAN RESET generation tracking prevents an older custom credential from overriding a later reset. Recovery defaults are still stored separately for local recovery as described in [LAN RESET](RPI_LAN_RESET.md).

The API requires current authentication, the same origin rules and `X-CIVI-Request` protection as other Web operations. Failed saving leaves the current password active. The response and application log do not include credentials. A successful in-memory verifier cache is invalidated when the password/reset generation changes, avoiding repeated expensive hashing for normal polling.

## Forgotten password: local password-only reset

From the Pi's attached keyboard/display terminal, as the normal CIVI user:

```bash
cd ~/civi-rpi-lxi
bash password-reset.sh
```

Type `PASSWORD RESET`, then enter a new 12–256 character password twice. Input is hidden. The old Web password is not required, and neither sudo nor the LAN helper is needed. SSH and redirected input are refused by this console entry point. No LAN, IP, hostname, discovery, radio or per-device recovery default setting is modified. Cancellation and mismatched input do not change the credential file.

Updated running CIVI reloads the saved hash within its normal approximately five-second monitoring interval. A stopped CIVI loads it on the next manual start; the launcher does not ask for another password because the new one has already been saved. LAN RESET can still restore the device recovery default later.

Creating an `auth-backup-*` directory alone has no effect on authentication: it neither moves nor changes credential files. No backup-directory operation is required for this password-only command.

## Verification — 2026-11-07

- Full Windows test suite: 216 passed, including password-only local reset, cancellation, mismatch and save-failure checks.
- Tests cover authentication/CSRF, mismatched and invalid passwords, persistence, previous-password rejection, save failure, local reset precedence and retaining a later custom password through the reset-monitor startup path.
- On the Pi, a separate mock-radio instance accepted a Web password change over verified TLS, rejected the old recovery password, saved a mode-600 hash file, and accepted the new password after application restart and the next reset-monitor pass.
- The temporary fixture and advertisements were stopped. Production credentials, radio connection and LAN configuration were not changed by these password tests.
- A further Pi mock-instance test reset only the password through the local administration function, verified that running CIVI accepted it without restarting, rejected the previous password, and left the recovery-default, reset-state and discovery/network files byte-for-byte unchanged. The attached-console prompt itself remains for manual confirmation.
