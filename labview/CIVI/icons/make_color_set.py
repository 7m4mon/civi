"""Export all 23 icons using the approved MON/red-line radio design."""
from pathlib import Path
from make_color_trial import draw_color
from make_complete_set import main

if __name__ == '__main__':
    main(
        output_dir=Path(__file__).resolve().parent/'complete-v2',
        renderer=draw_color,
        archive_name='CIVI-radio-icons-32-v2.zip',
        generator='make_color_set.py',
        design='Dark navy display with white text, #EC1E48 bottom display line, '
               'MON Morse code (-- --- -.) at the top, three black/dark-gray buttons, '
               'and a silver-rimmed dark-gray tuning knob with a black finger recess. '
               'No direction pointer. Regenerate this edition with ../make_color_set.py.',
    )
