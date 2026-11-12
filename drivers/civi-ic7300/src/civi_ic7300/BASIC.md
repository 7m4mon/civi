# Base commands and command audit (client 0.12.0)

SCPI_COVERAGE.md and scpi-coverage.json combine all supported gateway headers:
339 extended plus eleven base/special definitions, with directions, typed APIs,
documented spellings and explicit unsupported forms. Header aliases do not add
features. The scope is CIVI's ASCII interface, not all Icom hardware functions or
an IVI compliance determination. The source/parser hashes use normalized UTF-8
text so line endings do not change the inventory between Windows and Linux.

## Identification

`ivi_utility.identification: GatewayIdentification` is read-only and sends *IDN?.
The immutable result has four string fields:

| Field | Meaning |
|---|---|
| `manufacturer` | CIVI Project, the gateway manufacturer |
| `model` | CIVI/IC-7300 for a verified supported radio |
| `serial_number` | Configured CIVI instance identity, not a discovered Icom serial number |
| `software_revision` | CIVI gateway version, not the Python client or radio firmware |

CSV quoting is parsed and exactly four printable ASCII fields are required;
malformed responses raise ProtocolError. Manufacturer/model compatibility
properties use this same parser. The client version remains
`ivi_utility.driver_version`. Identity queries honor the typed status option.

`radio.firmware_revision: str` sends RAD:FIRM? and returns configured manual radio
firmware metadata or Unknown. It is not an automatic CI-V firmware query and does
not replace the fourth IDN field. The independent simulator returns Unknown;
mock TCP tests can configure metadata without changing a radio.

## Clear and completion

- `ivi_utility.clear_status() -> None`: *CLS;*OPC? clears this client's gateway
  error queue, including preexisting entries. It does not clear another client's
  errors, invent status registers, recover a quarantined serial link or reset
  the radio/network. With status ON, the explicit clear is allowed before its
  result status check; old errors do not abort the clear.
- `ivi_utility.wait_for_complete() -> None`: *OPC? waits for preceding processing
  and requires reply 1; other replies raise ProtocolError. Completion alone does
  not prove a prior setting succeeded. OFF leaves errors queued; ON/checked()
  obtains errors and raises DeviceError. Ordinary setters already await *OPC?.

Raw write/read operations remain caller-managed. Drain any raw query responses
before mixing typed and raw operations. Use STATUS.md for status policy and
QueryError behavior; *CLS is an explicit request to discard queue entries.

## Explicit PTT

- `operations.start_transmit() -> None`: RAD:PTT ON; requires the real gateway's
  transmit-enable configuration and ownership. It does not authorize transmission
  or renew an existing ownership deadline itself.
- `operations.stop_transmit() -> None`: RAD:PTT OFF; the gateway attempts to stop
  all CIVI-owned paths (including CW/voice/VOX/break-in/tuner) and PTT. It does not
  guarantee a stop after USB failure or control externally initiated transmission.
- `radio.transmitting: bool` remains read-only, using RAD:PTT?. No PTT property
  setter is added; the explicit start/stop methods express the requested action.

Both methods follow the status option. With checks ON, STOP still attempts before
reporting prior/new errors. OFF can leave a failed request queued without raising.
The real gateway retains its watchdog/disconnect handling. Offline simulation
models logical PTT state and checks its timeout lazily on I/O; close/reset clears
owned modeled paths. It does not emit RF. The gateway mock also emits no RF.

```python
from civi_ic7300 import CiviIc7300

with CiviIc7300(
    "TCPIP::unused::5025::SOCKET", options={"simulate": True}
) as d:
    print(d.ivi_utility.identification)
    print(d.radio.firmware_revision)  # Unknown
    d.operations.set_simulated_permissions(transmit=True)
    with d.checked():
        try:
            d.operations.start_transmit()
            assert d.radio.transmitting
        finally:
            d.operations.stop_transmit()
```

## Unsupported forms

The gateway does not implement *RST, non-query *OPC, status registers/SRQ,
self-test or *WAI. Unsupported forms are rejected, not silently translated.
`reset()` uses the documented RAD:RESET receive baseline and is not an alias for
*RST, an Icom Partial/All Reset or LAN RESET. SCPI_COVERAGE.md lists tested
unsupported probes and alternatives. VXI-11/HiSLIP, arbitrary CI-V passthrough,
binary-block/audio transport and OS/LAN administration are outside this client's
ASCII inventory; protected commands actually present in the catalog remain
included even when write permissions default OFF.

The audit verifies documented aliases through the actual gateway parser. The
standalone simulator supports the typed APIs, not every raw alias/relative
compound program. No physical radio/Pi test was performed for this release.
