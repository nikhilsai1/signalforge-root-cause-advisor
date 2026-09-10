# SOP-10: Valve Position Fault Response

**Applies to:** LINE1.VLV_01, LINE1.VLV_02, LINE1.VLV_03
**Monitored tags:** LINE1.VLV_01.POSITION_FAULT, LINE1.VLV_02.POSITION_FAULT

¶1. Purpose
Covers operator response to a valve position feedback fault, where the actuator's reported position does not match the commanded position.

¶2. Monitored Tags
- LINE1.VLV_xx.POSITION_FAULT: feedback deviates from command by more than 10% for over 15 seconds

¶3. Fault Response
If LINE1.VLV_xx.POSITION_FAULT fires, do not attempt to re-command the valve more than once from the HMI. Check for a pneumatic supply pressure drop at the local panel before assuming an actuator failure, most position faults on this line trace back to instrument air pressure, not the actuator itself.

¶4. Manual Override
If air pressure is confirmed normal and the fault persists, use the manual handwheel override only if the associated process tag (see SOP-08 or SOP-09 depending on line) requires immediate correction. Log the manual override in the shift log.

¶5. Escalation
Any valve fault lasting more than 15 minutes with air pressure confirmed normal should be escalated to instrumentation maintenance.
