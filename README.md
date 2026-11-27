# Quiet Keys Piano

A calm piano practice app from Gina Makes. Short sessions, keys always on screen, no counting, nothing to memorize.

© 2026 Gina Makes LLC

## What is here

- `www/index.html` is the whole app: lessons, songs, chords, and the on-screen piano.
- `ios/` is the iPad and iPhone shell (Capacitor), app ID `app.ginamakes.quietkeys`.
- `ios/App/App/AppDelegate.swift` listens to a USB piano keyboard (Core MIDI) and passes each key press to the lessons.

## Building without a Mac

- **Compile check:** GitHub → Actions → **iOS compile check** → Run workflow. Uploads nothing.
- **TestFlight:** GitHub → Actions → **iPad app to TestFlight** → Run workflow.
  Needs repository secrets `APPLE_TEAM_ID`, `ASC_KEY_ID`, `ASC_ISSUER_ID`, `ASC_KEY_P8_BASE64`.

## Lessons

Seven levels, from finding the first key to bass clef and seventh chords. The lesson list, songs, scales and chords are data near the top of the script in `www/index.html`.

- `tools/run-all-lessons.py` plays every lesson to the end in a headless browser and reports any that get stuck.
- The treble and bass clef shapes are outlines from Noto Music (SIL Open Font License 1.1).

## Songs

All melodies are traditional or public-domain pieces. They were written out from memory and need a play-through check against a trusted score.
