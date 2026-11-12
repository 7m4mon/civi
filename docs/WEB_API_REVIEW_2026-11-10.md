# Web / identification API review — 2026-11-10

Scope: LXI Device 1.6.2 G08 follow-up, applying the identification-related
parts of API 1.1. This is a limited implementation review, not an LXI conformity
or security certification. The official revisions and source hashes are recorded
in [the clause inventory](LXI_REQUIREMENTS_2026-11-10.md).

## Changes

- All responses now receive the same no-store, nosniff, frame-denial and
  same-origin Content Security Policy headers. Previously early authentication
  failures, HTTP exceptions and XML ProblemDetails bypassed some of these headers.
  Authentication challenges and method Allow headers remain intact.
- The Welcome and LAN pages have an explicit Hostname field. It uses the acquired
  mDNS name only while discovery is enabled, successfully registered and without
  a recorded discovery error. Otherwise it shows the LXI interface IPv4 address,
  or Not assigned. System hostname is separately labelled as OS configuration.
  CIVI does not claim to validate a unicast DNS name.
- The Pi LAN form shows the subnet mask corresponding to the prefix, updating
  on input and after Read wired LAN. /24 is shown as 255.255.255.0; the supported
  prefix range remains 1–32. The helper's addressing behavior is unchanged.
- Gateway identification returns XML 503 during service shutdown. A cached
  identified radio that is no longer connected returns XML 503 rather than a
  successful child identification. An unidentified radio returns XML 404.

## Readiness and interface contract

The instrument served by `/lxi/identification` is the CIVI gateway. This synchronous,
public GET requires no radio I/O, authentication or configuration changes. While
the gateway serves requests, radio disconnected/connecting/quarantined states do
not prevent a complete gateway identification response (200). Those states remain
visible on the Web page. No identified child is advertised in ConnectedDevices
when the service has cleared its radio identity. A known but unavailable child's
own identification returns 503. Gateway shutdown and unavailable identification
data return 503 with schema-valid, non-sensitive ProblemDetails.

LAN configuration trials are separate authenticated CIVI JSON operations. An
identification read neither completes nor confirms a pending trial and does not
return 202. `/health` retains its existing radio readiness meaning; it is not an
LXI API. Whether this gateway definition meets the final device-wide interpretation
of normal operation remains part of G08's final review, not a new conformity claim.

Successful identification responses use text/xml as specified by the identification
table. Schemas and ProblemDetails use application/xml. GET and HEAD are supported;
other methods return 405 with Allow. HEAD has GET's media type and length without
a response body. Conditional request headers cannot turn the live identity into
a stale cached 304. There is no XML request payload on these GET endpoints and
no newly introduced Content-Type or Accept restriction.

## Access-control coverage

The test inventory covers all 15 POST paths: Identify, discovery settings,
password change, six Pi helper actions (preview/apply/confirm/rollback/hostname/
Ping), and session/heartbeat/SCPI/serial/recovery/release. Adding a new POST route
without updating the inventory fails the test.

Every path is tested for missing credentials, malformed Basic authentication,
wrong password, missing X-CIVI-Request, a foreign Origin, and the old password
after rotation. No rejected operation is allowed to mutate settings. Existing
tests cover accepted operations, password persistence and helper semantics.
The public pages contain forms and information; their POST actions require
authentication. No permissive CORS policy or authentication bypass was added.

## Verification

- Windows full automated suite: **534 passed, 1 Linux-only skip**, 39.95 seconds.
- `tests/test_web_api_review.py` adds 12 cases, including a route-wide access
  matrix, public gateway reads in four radio states, child/shutdown errors,
  GET/HEAD/405/schema headers, actual-name fallback and escaping, unique HTML IDs,
  and subnet-mask behavior executed through the actual JavaScript with Node.
- Strict HTML5 parsing with html5lib 1.1: generated Welcome and LAN pages and
  bundled radio-control/help pages passed. The library was installed only under
  local tmp/html-review-libs, not in the gateway runtime. This is a parser check,
  not a complete W3C conformance or accessibility audit.
- Identification and ProblemDetails are validated against the bundled official
  XSDs; compatibility schema URLs remain unchanged.

Pi isolated-copy tests: **41 passed, 1 Node-only skip**, 36.08 seconds. The
Windows run executed that JavaScript test successfully. Pi test dependencies were
loaded from the existing tmp/lxi-test-libs directory; the runtime environment was
not changed. The independent test copy is tmp/web-api-review-20261110-222500.

## Production Pi follow-up

Deployed to /home/nom/civi-rpi-lxi, backing up changed files under
tmp/deploy-web-api-20261110-112800. Only CIVI was restarted, using the existing
manual desktop component launcher. Helper and panel remained running. No automatic
startup, privileged helper policy or network configuration changes were made.

Windows verified HTTPS on wired 192.168.73.2:443, trusting the existing public
certificate and validating its civi.local name. Numeric-IP certificate coverage
was not added and certificate validation was not disabled. Production checks:

- Welcome, LAN page, parent/connected-radio identification and both XSDs returned
  200 with the expected media types. Identification declared only eth0 as LXI.
- Hostname displayed civi.local.; the updated subnet-mask field was present.
- Identification HEAD returned no body; POST returned XML 405 with Allow;
  an unknown LXI resource returned 404; protected status without credentials
  returned JSON 401. Common no-store/nosniff/frame headers were present.
- LAN Normal, Identify OFF, attached panel connected and acknowledged.
- SCPI readback: 774000 Hz, AM, PTT OFF, no queued error. No radio settings were
  changed and no transmission was started.
- config.toml, saved Web authentication and saved network settings were verified
  byte-for-byte unchanged across deployment/restart. Both helper and CIVI remained
  ready and the existing panel process remained running.

This review does not repeat the earlier cable, DHCP or Identify physical trials.
Authenticated production mutations were not repeated: their access boundaries and
successful behavior were exercised in the isolated mock tests without disclosing
or resetting the saved production Web password.

## User browser display checks

The user confirmed the updated display on Windows and on Chrome on a smartphone.
The Windows browser/version and smartphone OS/version were not specified. This
records visual display checks only; it does not claim all authenticated settings
actions or disconnected/reconfiguration states were exercised on both devices.

## Still open

The remaining real-browser interaction/state checks, device-wide readiness semantics
in the final fixed product configuration, and the remaining G05 network lifecycle
tests remain open. LXIVersion, logos and certification wording remain deliberately
unclaimed. New headers and mock tests do not establish a full security assessment
or close all of G08.
