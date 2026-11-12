# Receive reset (client 0.10.0)

`ivi_utility.reset()` or constructor `reset=True` uses `RAD:RESET;*OPC?`.
It changes radio settings. It is not Icom Partial/All Reset, *CLS, power cycling,
or LAN RESET. The official IC-7300 CI-V supplement does not list a Partial/All
Reset command: https://www.icom.co.jp/support/manual/2557/.

The updated CIVI server requires a verified IC-7300 identity and performs one
serialized operation: PTT OFF; stop CW/voice output owned by CIVI, if any;
VOX/BK-IN/tuner OFF; verify receive;
scan stop; VFO mode and VFO A; both VFOs 14100000 Hz,
USB, DATA OFF, FIL2; 57 normal operating/scope settings captured after the user's
Partial Reset on 2026-11-08. These include Split/RIT/XIT OFF, zero RIT offset,
PRE1, AGC MID, AF gain raw 1 and RF gain raw 255. It reads back settings, display frequency/mode and
PTT before recording successful completion. A failed ACK or readback stops the
sequence immediately. A partial change is not rolled back automatically.

Memories, menu/calibration values, stored scope edges, serial and network
configuration are outside this baseline. It does not bypass menu-write permissions. This
baseline does not constitute a reset of every existing CIVI command.

The client now sends RAD:RESET;*OPC? and follows the status option. ON
checks preexisting/result errors; OFF leaves reset failures queued. Use checked()
for an explicitly verified reset. An older server's undefined-header error is
reported as DeviceError with checks ON. Reset uses a 30-second default timeout,
restores the normal timeout afterward, and never bypasses quarantine/recovery.
A transport timeout has an unknown outcome; inspect state before retrying.

Simulation resets the modeled frequency/mode without instrument I/O. Mock tests
verify the server baseline, unrelated-state preservation, failures and
serialization. On 2026-11-08 physical reset restored both VFOs and all 57 settings
after a temporary 1 kHz change. It completed in about seven seconds with PTT OFF;
214 non-clock menu readings remained unchanged. An idle CW-stop NAK found during
testing led to sending CW/voice stops only for owned output; owned failures still
abort reset. The normal five-second I/O timeout was restored after reset.
IVI conformity and registration are still not claimed.
