# CIVI implementation and completed test results

Review edition: **2026-11-12** · Author: **7M4MON / nomulabo**

CIVI delivers an IC-7300 USB CI-V gateway, SCPI/VISA transport, an authenticated local Web interface, Raspberry Pi instrument administration and a dedicated typed Python instrument driver. This page presents completed work and its supporting evidence for registration review. IVI registration and formal LXI/IVI conformance are not claimed.

## Delivered Python instrument-driver coverage

The driver implements **339 of 339 extended CIVI command definitions**, with a dedicated typed API for every supported direction. Including the 11 base/special headers gives **350 mapped canonical headers**. These are implementation inventories, not counts of independent physical tests. The public index contains **43 public/returned types and 352 constructors/members/fields**.

| Implemented API family | Delivered functions |
|---|---|
| Session and utility | Connect/close, identification, options, simulation, timeout, completion, errors, direct I/O and captured receive-profile reset |
| VFO and receiver | Selected/other VFO views, selection, exchange/copy, frequency, eight modes, DATA and filter selection |
| Gains and receiver processing | AF/RF/squelch, noise reduction/blanker, PBT, notch, CW pitch/speed, preamp/attenuator and related receive settings |
| Meters and status | S-meter raw value, squelch/overflow, power/SWR/ALC/compression/voltage/current and operating status |
| Spectrum scope | Controls, span/edges/reference, complete sweep retrieval and waveform metadata |
| Memory | Addressed records, names, frequency/mode/DATA/filter/tone/split/group fields, write/read/clear and selected-memory operations |
| Band stack | Addressed band/register records, typed serialization, read and write |
| Keyer | Eight stored text records and names, text read/write and supported command operations |
| Scan | Seven start enums, STOP/resume, ΔF widths, select assignment and ALL/★1/★2/★3 filter controls |
| Menu settings | Typed and catalog-driven access to all 216 menu selectors, with ranges and protected-operation gates |
| Transmit and operating controls | PTT state/control, TX Inhibit, power/modulation and other exposed operating controls with gateway permissions |
| Band edges | Factory/user counts and records, typed empty-slot handling and exposed protected write operations |

Sources: [complete extended mapping](PYTHON_DRIVER_COVERAGE.md), [350-header inventory](PYTHON_SCPI_AUDIT.md), [public signatures and contracts](../drivers/civi-ic7300/src/civi_ic7300/REFERENCE.md), [driver setup/examples](../drivers/civi-ic7300/README.md). The coverage boundary is the documented CIVI catalog; this does not assert every possible IC-7300 function is exposed.

## Requirement / implementation / completed test / result

Each row links to the detailed record. A pass applies to the named procedure and conditions. MAIN 1.41 and 1.42 results retain their original firmware context. Counts from overlapping campaigns are not summed.

| Requirement or behavior | Implementation | Completed procedure | Recorded result and evidence |
|---|---|---|---|
| VISA-compatible network control | LF SCPI TCP 5025 | Localhost TCP, PyVISA RAW SOCKET and authenticated HTTPS used with the radio | Commands, scope and concurrent operations succeeded ([Oct 18](TCP_VALIDATION_2026-10-18.md)) |
| Pi-hosted instrument | Pi 4 + USB-connected IC-7300 | Separate Windows client used TCP/PyVISA, changed/read/restored frequency and ran concurrent requests | 20 concurrent read/error pairs and 475-point sweep succeeded ([Oct 19](RPI_LAN_2026-10-19.md)) |
| Driver identity/core/receiver | Python 0.13.1 over Pi TCP | MAIN 1.41 core/receive and receiver-setting procedures; save and restore | 40 + 65 campaign checks passed ([receive acceptance](IVI_RECEIVE_ACCEPTANCE_2026-11-11.md)) |
| Menu access | 216 menu selectors | MAIN 1.41 descriptor/menu reads | All 216 menu reads succeeded ([record](IVI_RECEIVE_ACCEPTANCE_2026-11-11.md)) |
| Setting write/readback/restore | SCPI operating and menu setters | Earlier Windows CI-V campaign changed 233 targets, including 189 menu settings | Readback/restoration recorded; original rounding observations retained ([Oct 17](HARDWARE_2026-10-17.md)) |
| VFO control | Both relative views; frequency/mode/DATA/filter and swap | MAIN 1.42 bounds, eight modes, filters 1–3 and restoration | 57 physical and 57 simulation checks passed ([VFO](IVI_API_ACCEPTANCE_2026-11-12.md)) |
| VFO copy | A→B and B→A | Distinct initial records; copy, source preservation, repeated copy and restoration | 23 checks in simulation and hardware passed ([copy](IVI_VFO_COPY_2026-11-12.md)) |
| Storage read | Memory, band stack and keyer collections | 101 memory + 33 stack + eight keyer addressed reads | 142 physical reads and 200 associated local checks passed ([API acceptance](IVI_API_ACCEPTANCE_2026-11-12.md)) |
| Memory write/clear | Full 39-byte records | Empty memory 99; eight mode/split/DATA/tone/filter/group/name records; restore empty | 24 simulation and physical checks passed ([memory writes](IVI_MEMORY_WRITE_2026-11-12.md)) |
| Selected-memory commands | Store/display/copy/clear | Explicit MEM selection, operation/readback and restore | 29 simulation and physical checks passed ([selected memory](IVI_SELECTED_MEMORY_2026-11-12.md)) |
| Empty-memory behavior | Exact CI-V FF sentinels handled as no data | Empty memory selected; sample 03 FF / 04 FF; return to VFO | Connection remained active, Web showed empty, SCPI reported no-data and VFO readings returned ([empty memory](EMPTY_MEMORY_2026-11-12.md)) |
| Band-stack and keyer writes | Typed record and text setters | Save all 33 stack slots/eight keyer texts; write/read/immediately restore; compare backups | 89 simulation and physical checks passed; text storage only ([stack/keyer](IVI_SCAN_STORAGE_2026-11-12.md)) |
| Scope controls/data | Typed settings and complete waveform | MAIN 1.42 control/readback/restore, full sweep and fixed-edge reads | 72 checks passed; 475 points; 52 edge records; 14 controls restored ([scope](IVI_API_ACCEPTANCE_2026-11-12.md)) |
| Scan starts and stop | Seven start enums | Eight physical runs across VFO/MEM; observe movement and stable STOP samples | All eight runs showed movement and stable STOP; scratch memories restored ([scan operations](IVI_SCAN_STORAGE_2026-11-12.md)) |
| ΔF scan width | Seven supported half-spans | LSB ±5 kHz through ±1 MHz; verify sampled motion within bounds and stop | 33 physical checks passed ([scan settings](IVI_SCAN_SETTINGS_2026-11-12.md)) |
| Select-memory scanning | Select ON/OFF, assignments and filter | ALL/★1/★2/★3; check eligible memory frequencies; restore original ★1 | 34 physical checks passed; owner confirmed display/behavior ([scan settings](IVI_SCAN_SETTINGS_2026-11-12.md)) |
| Band-edge reading | Typed factory/user records | MAIN 1.42 read ten factory + 30 user records, including empty records | All 40 records; 49 checks passed after empty-slot decoder fix ([record](IVI_API_ACCEPTANCE_2026-11-12.md)) |
| TX Inhibit setting | Firmware 1.42 CI-V 16 66 | True/False readback and three invalid-type checks; restore | Five checks passed; no transmit start sent ([MAIN 1.42](IVI_TX_INHIBIT_2026-11-11.md)) |
| Receive reset | Captured normal operating profile | Restore both VFOs and 57 settings; compare protected menus | Reset completed; 214 non-clock menus unchanged ([reset](PARTIAL_RESET_CAPTURE_2026-11-08.md)) |
| Driver distribution | Buildable wheel and source | Clean install and read-only physical smoke | Installation and identity/read operations passed for the recorded artifact ([receive acceptance](IVI_RECEIVE_ACCEPTANCE_2026-11-11.md)) |
| HTTPS instrument pages | Primary Pi 443, optional 8443 | Deploy HTTPS and access instrument pages | PC/browser access confirmed ([HTTPS setup](RPI_HTTPS.md), [Web review](WEB_API_REVIEW_2026-11-10.md)) |
| Identification API | XML and locally served official XSD | Schema/content/header/access-control review | Recorded validation passed ([Web/API review](WEB_API_REVIEW_2026-11-10.md)) |
| Web fault states | Clear stale values and disable invalid actions | Disconnect, status retrieval failure and LAN confirmation expiry | State handling passed; owner confirmed stale-value clearing and disabled confirmation ([states](WEB_STATES_2026-11-10.md)) |
| DHCP lifecycle | NetworkManager wired automatic IPv4 | Physical eth0 acquisition, renewal with changed DNS/gateway, expiry and return | DHCP/AutoIP/Fault transitions and reacquisition verified; static IP restored ([DHCP](RPI_DHCP_ETHERNET_2026-11-10.md)) |
| Saved configuration | Persistent DHCP/static settings | Full Pi reboot and RESET from static to DHCP | Saved mode survived reboot, RESET acquired DHCP; original static IP restored ([boot](RPI_DHCP_BOOT_2026-11-11.md)) |
| Temporary LAN changes | Checkpoint + new-address confirmation | Apply changed address, confirm or allow rollback | New-address access and fallback confirmed ([LAN settings](RPI_LAN_SETTINGS.md)) |
| AutoIP communication | Automatic link-local + source-specific replies | Physical PC/Pi HTTPS and SCPI access | AutoIP HTTPS/SCPI succeeded; temporary test routes removed ([AutoIP TCP](RPI_AUTOIP_TCP_2026-11-08.md)) |
| Hostname/discovery collision handling | Acquired hostname and common service suffix | Physical peer collision; remove peer; full Pi reboot | civi-2.local and service (2) acquired and retained after reboot ([collisions](RPI_NAME_COLLISION_2026-11-11.md)) |
| Discovery after reconnect | Probe and advertise four services | Physical cable cycle; capture probes; fresh discovery/HTTPS/SCPI | Three hostname and service probes; four services advertised around six seconds; access passed ([reconnect](RPI_MDNS_RECONNECT_2026-11-11.md)) |
| Peer name resolution | Pi NSS/socket and mDNS | Outward .local and reverse-record tests; isolated allocated AutoIP peer TCP | Resolution and request/reply succeeded in recorded environments ([resolver](RPI_MDNS_RESOLVER_2026-11-11.md), [allocated peer](RPI_MDNS_AUTOIP_2026-11-11.md)) |
| mDNS/Ping persistence | Web enable/disable saved to Pi | Disable, reboot, verify, then re-enable | Owner confirmed disabled Ping after reboot and restored both controls ([progress](PROGRESS_2026-11-07.md)) |
| Unplugged boot and recovery | Saved static profile and LAN panel | Pi reboot with cable absent; manual app start; reconnect | Fault with cable absent; original static IP, Normal, HTTPS and SCPI returned ([boot](RPI_UNPLUGGED_BOOT_2026-11-08.md)) |
| Local configuration initialization | LAN RESET + recovery credentials | Reset; reboot with cable absent; reconnect | DHCP/AutoIP and authentication persisted; automatic address/discovery returned ([LCI boot](RPI_LCI_BOOT_2026-11-08.md)) |
| Local status / Identify | Attached display POWER ON, Normal/Fault and flashing Identify | Owner visual checks; cable removal during Identify; restart/stop | Power/status visible, Fault took priority, Identify restarted and stopped ([Pi checks](RPI_LXI_FIXES_2026-11-10.md), [readiness](LXI_READINESS_2026-11-11.md)) |
| Ethernet operation | Unrestricted auto-negotiation | Physical 100 Mbps full/half; restore gigabit auto-negotiation | Links and instrument access verified ([Ethernet](RPI_ETHERNET_2026-11-08.md), [readiness](LXI_READINESS_2026-11-11.md)) |
| Auto-MDIX applicability | Unmodified Pi 4 onboard PHY | Review BCM54213PE crossover-correction capability documentation | Auto-MDIX supported; non-support label clause does not apply to this configuration ([device boundary](LXI_DEVICE_CONFIGURATION.md#auto-mdix-applicability-decision)) |

## Review package and reproducibility

- [Full LXI clause audit](LXI_REQUIREMENTS_2026-11-10.md): 101 active Device RULE headings mapped in 175 audit rows, with clause references and linked evidence. These are audit inventory counts.
- [Public API reference](../drivers/civi-ic7300/src/civi_ic7300/REFERENCE.md), [command mapping](PYTHON_DRIVER_COVERAGE.md) and [menu inventory](IVI_MENU_VERIFICATION_2026-11-12.csv) provide traceability from interface to implementation.
- [Reconciled evidence records](IVI_VERIFICATION_RECONCILED_2026-11-12.json) retain the classification and scope of the 352 indexed API entries.
- Acceptance tools in `tools/ivi_*_acceptance.py` preserve the read/change/readback/restore procedures. Physical instrument execution is separate from automated regression tests.
- The publication regression run on November 12 completed with **619 passed, one Linux-only skip** (47.44 seconds). Strict typing passed for all 12 Python driver source files. The six generated documentation/evidence consistency checks also passed. The recorded Pi full run on November 11 was **594 passed, ten environment skips**; later Pi checks are recorded individually. They are separate runs, not a combined total.

The source, package documentation, examples, mock backend, dated test records and clause mapping form a reviewable implementation dossier. Detailed historical records are retained with their original conditions and observed corrections.
