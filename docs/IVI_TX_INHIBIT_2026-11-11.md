# TX Inhibit on IC-7300 MAIN 1.42 — 2026-11-11

The owner updated MAIN firmware from 1.41 to **1.42** and restarted CIVI after
the USB interruption quarantined the old link. The subsequent driver test
connected successfully. Firmware version is owner-reported, not obtained by CI-V.

## Method and result

Source client 0.13.1 used TCP SOCKET to the Pi CIVI gateway. PTT, VOX, break-in
and tuner were verified OFF before changes. A wire allowlist permitted only
`RAD:TXINHIBIT ON` and `RAD:TXINHIBIT OFF` writes; no transmission-start,
memory/menu/calibration/power commands or permission changes were permitted.
The test saved its baseline before the first write and restored it in finally.

| Case | Result |
|---|---|
| Initial `operations.transmit_inhibited` | False; query accepted |
| Set True, read back | True; PTT OFF |
| Set False, read back | False; PTT OFF |
| Inputs `1`, `"ON"`, `None` | Type/value rejection before any I/O |
| Restore/read back initial value | False |
| Error queue after restoration | Empty |

The five parameter checks passed in both logical simulation and the physical
1.42 setup. Selected VFO stayed **928000 Hz / AM / DATA OFF / FIL2**, other VFO
stayed **14100000 Hz / USB / DATA OFF / FIL2**. The full saved baseline matched
after restoration. No PTT start was sent; every sampled PTT state was OFF. This
does not test suppression of actual RF transmission by deliberately pressing PTT.

## Interpretation

The earlier [MAIN 1.41 test](IVI_RECEIVE_ACCEPTANCE_2026-11-11.md) received NAK
for `16 66` across AM/USB/CW/LSB. The official
[1.42 update information](https://www.icomamerica.com/uploads/support/firmware_driver/IC-7300_ENG_FirmUpInfo_0.pdf)
documents addition of this command in 1.42. The new successful get/set/readbacks
confirm availability on the updated unit. The 1.41 observation is retained as
firmware-dependent evidence, not relabeled as a success.

Other APIs tested on 1.41 have not all been rerun on 1.42. This focused follow-up
does not complete IVI's whole-driver unit-test procedure or registration.

## Reproduction and evidence

Opt-in manual tool, never run by startup or pytest:

```sh
python tools/ivi_tx_inhibit_acceptance.py --simulate --set-inhibit --output tmp/inhibit-sim.json
python tools/ivi_tx_inhibit_acceptance.py --firmware 1.42 --set-inhibit --output tmp/inhibit-physical.json
```

Private results and client source hashes are in `tmp/ivi-txinhibit-20261111`.
No gateway configuration, firmware metadata setting or authentication was changed
by this test. The firmware update itself was performed by the owner.
