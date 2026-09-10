# SOP-09: Tank Level Deviation Response

**Applies to:** LINE1.TANK_01, LINE1.TANK_02
**Monitored tags:** LINE1.TANK_01.LEVEL_HIGH, LINE1.TANK_01.LEVEL_LOW, LINE1.TANK_02.LEVEL_HIGH

¶1. Purpose
Covers operator response when a surge tank level moves outside its normal operating band.

¶2. Monitored Tags
- LINE1.TANK_xx.LEVEL_HIGH: level above 85%
- LINE1.TANK_xx.LEVEL_LOW: level below 15%
- Normal operating band: 30-75%

¶3. High Level Response
If LINE1.TANK_xx.LEVEL_HIGH fires, check the discharge pump for that tank (SOP-08) for a low-flow condition first, a backed-up downstream pump is the most common cause of tank overfill. Open the manual bypass only if level continues to rise above 92% and no pump fault is found.

¶4. Low Level Response
If LINE1.TANK_xx.LEVEL_LOW fires, check the upstream feed pump and conveyor (SOP-07, SOP-08) for a stoppage before assuming a leak. A stopped upstream conveyor starving the feed line is more common in this system than a physical leak.

¶5. Escalation
Sustained high or low level for more than 10 minutes after corrective action should be logged and escalated, do not silence the alarm without a corresponding tag change.
