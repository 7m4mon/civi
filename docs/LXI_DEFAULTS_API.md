# Factory names and identification API

Implemented for Device Specification 1.6.2 rules 9.5.7/9.5.8 and the identification-related portions of rule 10.2. This closes these specific implementation gaps, not all LXI requirements.

## Empty fields on the LAN page

After authenticating, save an empty or whitespace-only Description or System hostname:

| Field | Factory value | Scope |
|---|---|---|
| Description / service name | `CIVI <serial_number>`; for example `CIVI CIVI-0001` | Saved in `.civi-network.json`, then advertised; reused at future starts |
| System hostname | `civi` | Saved immediately through the Pi helper; applies to the whole Pi |

These defaults come from `civi/defaults.py` and the device identity, independently of a custom Description in config.toml, saved user names or names acquired after a collision. Whitespace-only input is treated as empty. Nonempty values retain the existing validation rules.

The UI allows blank input, explains its meaning and displays the resolved value after saving. Authentication, CSRF checks, transmission guards and the pending IPv4-change guard still apply. Hostname changes do not alter IPs or create checkpoints. A write/readback failure is not reported as success; the existing hostname restoration behavior is retained.

This operation differs from LAN RESET: LCI retains the last user-configured names and resets collision-derived names back to those desired names. An explicit blank-field save makes the factory value the new desired name. Network conflicts may still add a suffix to the acquired name, and certificates are not regenerated.

Restart **both the LAN helper and CIVI** after installing these source changes. Refresh the Web page to load the updated form/script. No Pi reboot or automatic startup is required.

## Schema URLs and XML errors

- `/lxi/schemas/InstrumentIdentification/2.0`: identification XSD, now used in identification XML schemaLocation.
- `/InstrumentIdentification/2.0`: unchanged compatibility URL, serving identical bytes.
- `/lxi/schemas/LXIProblemDetails/1.0`: official problem-details XSD, copied byte-for-byte from [the LXI schema site](https://lxistandard.org/schemas/LXIProblemDetails/1.0).

Successful gateway and connected-radio identification responses use `text/xml`, matching the API 1.1 identification table. Errors on standardized identification/schema resources use `application/xml` and schema-valid `LXIProblemDetails` with the HTTP status phrase as Title. Status codes and method `Allow` headers are preserved. Unexpected failures return 503 without exposing internal exception messages. CIVI's `/api/...` endpoints retain JSON errors.

Identification is a public read of the gateway's current identity and cached connected-device information. A disconnected radio does not by itself mean the gateway is unready; an unidentified connected radio returns 404 on its own identification endpoint. This read operation has no pending reconfiguration and does not return 202. No LXI version or certification claim was added.

## Verification

Automated tests cover authenticated blank/whitespace Description reset, persistence/reload despite custom configured names, failed-save preservation, hostname resolution through the helper and preservation of unrelated network fields. API tests verify identical schema aliases, schema-valid 404/405/503 responses, Allow preservation, safe failure messages and the unchanged JSON authentication errors. The full suite passed 235 tests with one skipped before the final schema-read adjustment; affected API tests are rerun after it.

Deployed to `/home/nom/civi-rpi-lxi`. A separate Pi mock server on HTTPS 18444 / SCPI 15031 passed certificate-verified checks from Windows: identical schema URLs, schema-valid 404/405 errors, Allow header, custom/blank/whitespace Description saves and unchanged JSON authentication errors. The saved fixture Description was checked on disk. A direct call through the updated Pi transaction code resolved whitespace hostname to `civi` while the actual hostname already equaled `civi`; the snapshot remained unchanged. Actual changed-name restoration remains covered by fake-manager tests and awaits user Web verification after helper restart.

The user subsequently restarted the updated processes and confirmed both Description and System hostname blank-field restoration through the production Web page. This supersedes the earlier pending Web verification above. The fixture was stopped, leaving the production app/helper/panel and network settings intact. A source deployment does not change a running Python process; later installations require the manual restart described above. At this feature's implementation stage the full suite had 235 passed, one skipped; 14 affected API tests passed again after the final schema-read adjustment. The final same-day suite reached 257 passed, one skipped.

## Later Web/API review

See [the 2026-11-10 follow-up](WEB_API_REVIEW_2026-11-10.md) for gateway shutdown/child unavailability semantics, common response headers, all mutation-route access tests and production Pi verification. The earlier test counts above are historical.
