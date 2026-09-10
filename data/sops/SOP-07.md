# SOP-07: Conveyor Jam & Stoppage Response

**Applies to:** LINE1.CNV_01, LINE1.CNV_02, LINE1.CNV_03
**Monitored tags:** LINE1.CNV_01.SPEED_LOW, LINE1.CNV_01.JAM_DETECTED, LINE1.CNV_01.STOPPED

¶1. Purpose
This procedure covers operator response when a conveyor reports a jam, an unexpected stop, or a speed deviation from setpoint.

¶2. Monitored Tags
- LINE1.CNV_xx.STOPPED: conveyor unexpectedly stopped
- LINE1.CNV_xx.SPEED_LOW: belt speed below setpoint
- LINE1.CNV_xx.JAM_DETECTED: jam flag from load-cell/torque threshold

¶3. Jam Detected Response
If LINE1.CNV_xx.JAM_DETECTED fires: stop the conveyor at the local isolator before inspecting. Clear the physical obstruction. Do not reset the drive until the belt path is visually confirmed clear. Reset via HMI, confirm the conveyor returns to normal run state within 10 seconds of restart command.

¶4. Speed Deviation Response
If LINE1.CNV_xx.SPEED_LOW persists for more than 30 seconds with no jam flag, check the upstream motor and drive (see SOP-14) before assuming a mechanical fault on the conveyor itself, a starved or overloaded drive is a more common root cause than the conveyor mechanism.

¶5. Escalation
If the same conveyor jams more than twice in one shift, log a maintenance ticket, do not continue resetting indefinitely.
