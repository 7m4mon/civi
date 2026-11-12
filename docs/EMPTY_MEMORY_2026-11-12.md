# Empty displayed memory: continuous connection — 2026-11-12

On IC-7300 MAIN 1.42, displaying empty ordinary memory 99 returned complete
addressed `03 FF` and `04 FF` frames for operating frequency and mode. The old
decoder treated these as malformed data and quarantined the connection.

## Implemented behavior

Only the exact single-byte `FF` response to operating-frequency/mode reads now
means no available value. The backend returns `None` and remains connected.
Other invalid lengths, BCD, modes and filters retain their existing error and
quarantine behavior. Timeouts and uncertain response ordering are unchanged.

Background polling clears obsolete frequency/mode values, preserves radio
identity, and continues S-meter and PTT monitoring. Web status exposes the
affected names in `unavailable_values`. The local Web interface displays
`Not set (empty memory)` and `Not set`; connected controls remain available.
The next valid VFO readings replace these labels automatically.

SCPI frequency/mode queries have no numeric/enum value in this state. They
return the existing `ERROR` sentinel and queue `-230,"No operating frequency
(CI-V FF; empty memory)"` or the corresponding mode message. This reports a
data-availability condition without stopping the connection. A background poll
does not fill the SCPI error queue just because memory is empty. No fabricated
zero-Hz value or stale value is returned.

## Verification

- Windows complete suite: **619 passed, one Linux-specific skip**.
- Regression tests cover both exact FF sentinels, valid values on the next
  query, malformed payloads still quarantining, cache clearing, identity and
  PTT continuity, SCPI error framing, and Web label/connected-control recovery.
- Physical Pi gateway / IC-7300 MAIN 1.42: selected empty channel 99 and entered
  memory mode. Three samples, after background-poll intervals, returned ERROR
  with -230 for both queries, PTT OFF, verified HTTPS health `radio=connected`,
  and empty error queues after consuming the two expected query errors.
- Returned to VFO mode: frequency 927000 Hz, AM, PTT OFF, channel 99 still empty,
  no SCPI error and HTTPS health still connected. No Recover connection or app
  restart was needed when switching back from empty memory.

No memory contents, write permissions or RF-start settings were changed. The
remembered selected memory is 99. Final VFO mode is restored. The Web JavaScript
behavior was executed with a regression-test DOM; the physical checks verified
SCPI and HTTPS health, not a new owner visual acceptance of the browser labels.

Private evidence: `tmp/ivi-memory-write-20261112/empty-memory-fixed.json`, with
the original wire evidence in `empty-frequency-raw.json`. See also
[the memory write/read/clear record](IVI_MEMORY_WRITE_2026-11-12.md).
