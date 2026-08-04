Changelog

All notable changes to this project are documented here. Format loosely follows Keep a Changelog.

Note on versions prior to 0.7: No formal versioning existed during initial development (2025). The entries below for v0.5–v0.6 are reconstructed after the fact, based on Kanban card history and best recollection, for the sake of a more complete project history. Treat exact ordering and dates as approximate.

[Unreleased] — v0.8 (in progress)

Planned: see project Milestones for full scope.

[0.7] — Initial Playable Release

The baseline version used to complete a full playthrough of Dark Souls 3 using only the GoCube Edge as a controller.

Added
Continuous yaw drift compensation, layered on top of the vector-projection orientation system
Yaw isolation/lock behavior, an attempt to prevent yaw miscalculation during combined pitch/roll movement
Known Issues
Yaw axis drift over time, worsened by forward pitch; partially mitigated via manual recenter hotkey (added 0.6)
Movement and camera control conflict above ~35° pitch: movement itself still works correctly, but the yaw isolation lock combined with ongoing drift compensation causes unwanted camera turning while moving
Initial BLE device detection occasionally fails intermittently; connection itself is reliable once detection succeeds
Requires manual editing of source code to set cube MAC address and key mappings (no config file yet)
[0.6] — Orientation Math Rework (reconstructed)
Added
Major architectural rework of gyroscope orientation calculation: replaced quaternion-to-Euler-angle conversion with direct gravity-vector projection, eliminating gimbal lock and axis coupling present in the 0.5 approach — undertaken while investigating early yaw drift observations
Manual recenter hotkey (Numpad 5) added as an early stopgap once yaw drift was first noticed, resetting gyroscope zero/neutral position on demand
Notes
The vector-projection rework was believed to improve drift severity and/or orientation stability at higher tilt angles compared to the prior Euler-angle approach; the exact degree of improvement was not precisely documented at the time
[0.5] — Core Functional Build (reconstructed)

The point at which the game became playable-ish for the first time, combining working face-turn input with early gyroscope-based movement.

Added
BLE communication with GoCube Edge via the Bleak library, replacing the original browser-based Web Bluetooth approach (adapted from Ignisco's Smart Cube Gaming Controller repo)
Protocol parsing for MsgRotation and MsgOrientation packets, including checksum validation
Face turn detection for all 12 possible cube face turns (direction-aware)
Keyboard/mouse input emulation via the Windows SendInput API (directinput.py) — initial attempt with DirectInput-style input was not registered by the target game window and was replaced with SendInput press/release commands
Resolved gyroscope data parsing failure: orientation payloads were found to be ASCII-encoded text (not raw binary), unblocking all gyroscope functionality (see BUG-002)
Early gyroscope-based movement and camera control using quaternion-to-Euler-angle conversion
Priority-based input queue system with anti-ghosting protection, resolving inconsistent/dropped face-turn inputs during rapid sequences (see BUG-003)
Known Issues (at the time)
Euler-angle approach prone to gimbal lock and axis coupling at higher tilt angles
