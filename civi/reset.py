"""Documented receive baseline, not an Icom Partial/All Reset.

Executed by the shared service worker as one fail-fast queue operation.
No menu, memory, calibration, power on/off, link or network settings are written.
"""

import json
from pathlib import Path

PROFILE = json.loads((Path(__file__).with_name('profiles') / 'ic7300-reset.json').read_text(encoding='utf-8'))
FREQUENCY_HZ = PROFILE['frequency_hz']
MODE = PROFILE['mode']

STOP_COMMANDS = (
    ("RAD:CW:STOP", None),
    ("RAD:VOICE", "STOP"),
    ("RAD:VOX", "OFF"),
    ("RAD:BKIN", "OFF"),
    ("RAD:TUNER", "OFF"),
)

BASELINE_COMMANDS = (
    ("RAD:SCAN:STOP", None),
    ("RAD:VFO:ENABLE", None),
    ("RAD:VFO:SELECT", "A"),
    *((header, f'{selector},{value}')
      for selector, vfo in zip(('SELECTED', 'OTHER'), PROFILE['vfos'])
      for header, value in (('RAD:VFO:FREQ', vfo['frequency_hz']),
                            ('RAD:VFO:MODE', vfo['mode_data_filter']))),
    *((item['header'], (item['selector'] + ',' if 'selector' in item else '') + item['value'])
      for item in PROFILE['settings']),
)

VERIFY_COMMANDS = (
    ("RAD:VOX", None, "OFF"),
    ("RAD:BKIN", None, "OFF"),
    ("RAD:TUNER", None, "OFF"),
    *((header, selector, str(value))
      for selector, vfo in zip(('SELECTED', 'OTHER'), PROFILE['vfos'])
      for header, value in (('RAD:VFO:FREQ', vfo['frequency_hz']),
                            ('RAD:VFO:MODE', vfo['mode_data_filter']))),
    *((item['header'], item.get('selector'), item['value']) for item in PROFILE['settings']),
)
