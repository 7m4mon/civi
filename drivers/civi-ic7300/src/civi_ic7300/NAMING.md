# Driver naming

| Role | Value |
|---|---|
| Author / current driver_vendor | 7M4MON |
| Planned applicant | nomulabo, individual developer |
| Controlled manufacturer / model | CIVI Project / CIVI/IC-7300 |
| Physical radio | Icom IC-7300 |
| Preferred vendor abbreviation | NL; NM as fallback |

After abbreviation assignment, the proposed identifier is `CiviIc7300_NL`, distribution `civiic7300-nl`, import `civiic7300_nl`, root class `CiviIc7300`. Current development imports remain `civi_ic7300`. Final naming is tracked by D-01/REG-01 in the [completion plan](https://github.com/7m4mon/civi/blob/main/docs/IVI_6_1_COMPLETION_2026-11-12.md).

The first token identifies the controlled instrument manufacturer. When it differs from the driver vendor, the final token identifies the driver vendor. Distribution/import characters agree apart from allowed separators; Introduction uses the complete DriverIdentifier.

Sources: [IVI Python naming](https://github.com/IviFoundation/IviDrivers/blob/main/IviDriverPython/1.0/Spec/IviDriverPython.md#driver-identifier-and-driver-class-name),[VPP-9](https://www.ivifoundation.org/downloads/VPP/vpp9_4.35_2024-08-08.pdf).
