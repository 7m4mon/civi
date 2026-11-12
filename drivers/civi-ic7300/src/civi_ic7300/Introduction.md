# Introduction to CiviIc7300 (experimental identifier)

## Driver Documentation

STYLE.md describes public naming, layout, repeated capabilities and compatibility.

`README.md` in the distribution provides initial setup. `API.md` documents the
implemented API and SCPI mapping. `COMPLIANCE.md` records package metadata and test environments. These documents are bundled alongside the importable source. REFERENCE.md
and public-api.json index public members; EVIDENCE.md defines verification scope.
The prescribed Foundation notice is in IVI_NOTICE.md and REFERENCE.md.

## Driver Source Code and Examples

The distribution contains Python source. The repository also contains
`tests/test_python_driver.py` and the README examples. From the repository root:

```console
python -m pip install build
python -m build ./drivers/civi-ic7300
python -m pip install ./drivers/civi-ic7300/dist/civi_ic7300-0.13.1-py3-none-any.whl
```

Use a clean virtual environment to test installation. No C compiler is needed.
The gateway and driver are separate distributions; installing this driver does
not launch, upgrade, or configure CIVI or Raspberry Pi network services.

## Connecting to the Instrument

Use Python 3.11+ with a running CIVI/IC-7300 gateway. Import `CiviIc7300` from
`civi_ic7300`, then construct it with `TCPIP::host::5025::SOCKET`. Python scripts,
interactive shells and IDEs use the same API. Always use a context manager or
call `close()`. API.md also documents INSTR location forms, which select raw
TCP 5025; no HiSLIP/VXI-11 transport is added. This package does not install
NI MAX discovery plugins.

## Configuring Instrument Settings

`radio.frequency_hz` and `radio.mode` select settings on the currently selected
VFO. Setters append `*OPC?` to wait for CI-V completion. `vfos["SELECTED"/"OTHER"]`
provides relative VFO views; select A/B with `vfos.select()`. `gains`, `meters`,
receiver settings on `radio` and `scope` provide the controls listed in CONTROLS.md.
API.md documents units, selectors, arguments and record formats.

## Configuring Driver Settings

Initialization accepts `simulate` and `query_instrument_status` options as
booleans in a dictionary or as comma-separated `key=true/false` strings.
Unknown options are rejected. `ivi_utility.query_instrument_status_enabled`
changes status checking. `ivi_direct_io.io_timeout_ms` changes the I/O timeout.
Simulation is fixed at construction and defaults to false.

## Direct I/O

`ivi_direct_io` provides ASCII line I/O. `query()` performs an atomic write/read
under the driver session lock. Separate raw write/read calls each hold the lock
but the pair is not atomic: callers must synchronize such pairs. Responses are
LF-framed, at most one MiB; no binary block protocol is supplied.

## Instrument Command Coverage

## Known Issues

See COMPLIANCE.md. `reset()` and constructor `reset=True` use the receive
baseline documented in Reset.md, captured and verified with the physical
IC-7300 on 2026-11-08. It is not a complete Icom Partial/All Reset and does not send `*RST`.

## Contacting Support

Author: 7M4MON. Source and issue reporting:
[GitHub](https://github.com/7m4mon/civi/issues).

## Release review

NAMING.md records conditional vendor-abbreviation proposals and the compatibility
plan; current import names remain provisional and unchanged.
AUDIT.md records the first Core/Python review and unresolved deviations. The
draft prescribed filename uses provisional CiviIc7300; it does not establish
a registered VPP-9 identifier. DriverOptions supplies typed constructor switches.

STATUS.md documents 0.10.0 status-option behavior, checked() blocks and
QueryError migration. Raw I/O does not consume the error queue automatically.
