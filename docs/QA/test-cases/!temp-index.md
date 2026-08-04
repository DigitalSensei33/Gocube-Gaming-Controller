BLE

BLE-01 — Cold-start connection
BLE-02 — Warm-start connection (cube already awake before launch)
BLE-03 — Mid-session disconnect/reconnect

FACE

FACE-01 — All 12 face turns detected correctly
FACE-02 — Sprint/dodge (U/U') interaction, including auto-release-sprint-on-dodge
FACE-03 — Rapid combo sequence, no ghosting

GYRO

GYRO-01 — Movement threshold accuracy (pitch/roll)
GYRO-02 — Camera/yaw threshold accuracy
GYRO-03 — Calibration from cold start
GYRO-04 — Raw orientation packet decodes to valid quaternion values (added later, surfaced by the ASCII-parsing bug retrospective)

QUEUE

QUEUE-01 — Anti-ghosting under rapid input
QUEUE-02 — Priority ordering (critical input during a queued lower-priority input)
QUEUE-03 — Input latency under load

HUD

HUD-01 — Live readings match physical orientation
HUD-02 — HUD reflects active movement/camera state accurately
HUD-03 — Toggle hotkey shows/hides HUD correctly (depends on the not-yet-built toggle feature — #26)
