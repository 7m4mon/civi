# Status policy and migration (client 0.10.0)

All typed APIs now follow `ivi_utility.query_instrument_status_enabled` (alias
`query_instrument_status`), including protected menu/storage/band/scan/operation
writes, scope start/stop and reset. The default remains false. Gateway permission
checks, transmit ownership, maximum duration and disconnect stops are unchanged.

| Mode | Behavior |
|---|---|
| OFF | No automatic SYST:ERR? traffic. Setters await *OPC?, which proves processing completion, not radio acceptance. A queued permission/NAK/serial error may remain without an exception |
| ON | Typed I/O checks errors after operations. Protected mutations also check preexisting errors. DeviceError reports extracted queue entries |
| `with device.checked():` | Temporarily selects ON and restores the previous setting, even on exceptions; locks the entire block to this session |
| Explicit error_query/all/raise_on_device_error | Always available, independent of the option |
| Raw query / Direct I/O | No automatic status traffic, including inside checked() |

## Explicit checked blocks

```python
from civi_ic7300 import CiviIc7300, DeviceError

with CiviIc7300(
    "TCPIP::unused::5025::SOCKET", options={"simulate": True}
) as d:
    try:
        with d.checked() as checked:
            checked.menus.integer_item(2).value = 5
    except DeviceError as error:
        print(error)  # Default menu permission remains disabled.
    assert not d.ivi_utility.query_instrument_status_enabled
```

`checked() -> ContextManager[Self]` yields the same driver. Entry/exit cause no
instrument I/O. Nested blocks restore their enclosing policy. Other threads using
this session wait until the block exits; other clients/local controls are not
locked out. Raw I/O remains explicit and caller-managed.

With checks ON, STOP/OFF collects prior errors, attempts the stop, then reports
both prior/new errors. With checks OFF, it sends the stop without inspecting the
queue. Acknowledgement alone does not guarantee that RF has stopped; use ON or
checked(), inspect supported radio state and retain the gateway safeguards.

Scope start with checks ON retains staged failure handling and transfer-setting
restoration attempts. OFF sends STREAM then ENABLE without checking their queued
errors or promising restoration. `write_and_read` with OFF can read the unchanged
value after a denied write. It does not infer write success from that value.

## Query errors and raw I/O

`QueryError(RuntimeError)` is raised for the gateway's lone ERROR sentinel. It
preserves the error queue and keeps a healthy connection open. With status OFF,
typed failed queries also raise QueryError without an automatic queue query.
Read `ivi_utility.error_query()` explicitly for the code/message. With status ON,
typed failed queries obtain detailed errors and raise DeviceError when present.
Raw `device.query()` always raises QueryError for ERROR, regardless of the status
option; raw read_string/read_bytes return the bytes/text supplied by the gateway.

Malformed framing remains ProtocolError; transport failures close the session.
Neither is suppressed by status OFF. A failed SYST:ERR? is itself a protocol
failure. The client does not fabricate a device error code when the queue has
not been read.

## Migration from 0.9.x and earlier

Earlier protected APIs checked errors even with the option OFF. To retain that
behavior, explicitly enable `options={'query_instrument_status': True}` or wrap
the calls in checked(). Use checked() for a write/readback/restore sequence whose
failures must stop later steps. The gateway's permissions must still be enabled
separately; checked() does not authorize writes or transmission.

For reset, both modes send RAD:RESET;*OPC? and preserve the reset-specific timeout.
ON checks the queue before/after; OFF leaves reset errors queued. No *RST, *CLS or
LAN RESET command is substituted. Full IVI conformance remains unclaimed; this
release addresses the status-policy finding, not every remaining audit item.
