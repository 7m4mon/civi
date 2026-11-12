# Manual desktop launch on Raspberry Pi

Double-click **CIVI** on the Pi desktop to start the LAN helper, CIVI server and local panel. Startup remains manual: no login autostart, systemd unit or scheduled task is installed.

The launcher waits for the helper, then the SCPI server, and opens the panel. The helper and CIVI each have a separate log terminal. If sudo asks for authentication, enter the **Linux/sudo password in the CIVI LAN helper terminal**. If CIVI has no saved Web credential, enter the Web password in the CIVI server terminal. Passwords are not embedded in the shortcut.

Existing healthy helper/server processes are reused. A panel from the same user and configuration is reused too; another checkout's panel is not mistaken for this one. Clicking again does not restart an existing CIVI. Concurrent launcher runs are locked out, and an occupied SCPI port belonging to another identity/configuration is reported rather than reused.

Stop CIVI and the helper using **Ctrl+C in their respective terminals**. The component launcher allows their cleanup to finish; the helper also handles terminal hangup/termination by removing its socket. Close the panel window separately. Closing the initial startup terminal after startup does not stop the panel. Panel startup errors are recorded in `tmp/desktop/panel.log`.

## Install or recreate the icon

As the normal Pi desktop user, without sudo:

```bash
cd ~/civi-rpi-lxi
bash desktop.sh --install
```

This writes an executable `CIVI.desktop` into the directory reported by `xdg-user-dir DESKTOP`. The shortcut contains an absolute path to this checkout. After moving the checkout, run the installation command again. On desktops asking whether to execute/trust the launcher, choose the launch option. The file uses the standard [Desktop Entry Exec format](https://specifications.freedesktop.org/desktop-entry/latest/exec-variables.html).

You can also start all components from a Pi graphical terminal:

```bash
cd ~/civi-rpi-lxi
bash desktop.sh
```

This launcher targets the tested Pi desktop with LXTerminal and the graphical session's existing DISPLAY/Xauthority. It does not invent `DISPLAY=:0` for plain SSH sessions or weaken display authentication. Separate existing scripts `start.sh` and `panel.sh` remain usable.

Read-only status inspection, including over SSH:

```bash
cd ~/civi-rpi-lxi
bash desktop.sh --check
```

The check verifies helper guard availability, the configured CIVI SCPI identity and the local panel process. It does not transmit or change radio settings. An existing unresponsive helper socket is reported and is not automatically deleted.

## Starting with the radio powered off

The three programs can start while the radio is unavailable. The launcher checks gateway readiness, not whether the radio has answered. If the serial port opens but a CI-V request times out, the existing quarantine protection remains in effect: turning on the radio alone does not clear it. Follow **CI-V connection settings → recovery confirmation → Recover connection** in the Web after checking/resetting the radio/link. Clicking the desktop icon again reuses the server; it does not bypass quarantine or reset the radio.

## Verification — 2026-11-08

Installed `/home/nom/Desktop/CIVI.desktop` on the Pi's labwc/PCManFM desktop. The user launched it and confirmed the panel appeared. Read-only checks then confirmed helper and CIVI ready, ports 443/8443/5025 listening, the attached panel connected/acknowledged and LAN Normal at `192.168.73.2`. A later radio power-on found the documented quarantine from starting with no radio response; radio readiness is separate from successful component launch.

After the user selected **Recover connection**, SCPI identified `CIVI/IC-7300`, read frequency `774000` Hz, mode `AM` and S-meter raw `75`, with `0,"No error"`. These were read-only checks; no frequency/mode/transmit setting was changed.

A second launch reused all three components, preserving the same panel PID. Automated tests cover argument/path quoting, reuse without extra processes, panel user/configuration matching, rejection of another instrument on the SCPI port, and allowing cleanup after Ctrl+C: **271 passed, 1 skipped** in the full Windows regression suite. No automatic startup or sudo policy changes were made.
