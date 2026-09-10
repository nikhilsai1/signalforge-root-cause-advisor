# SOP-12: Cooling Fan & Preheater Temperature Response

**Applies to:** LINE1.FAN_01, LINE1.HEATER_01
**Monitored tags:** LINE1.FAN_01.TEMP_HIGH, LINE1.HEATER_01.TEMP_HIGH, LINE1.FAN_01.STOPPED

¶1. Purpose
Covers operator response to high-temperature alarms on the cooling fan intake and preheater.

¶2. Monitored Tags
- LINE1.FAN_01.TEMP_HIGH: intake air temperature above 45C
- LINE1.HEATER_01.TEMP_HIGH: element temperature above 180C

¶3. Fan Temperature High Response
If LINE1.FAN_01.TEMP_HIGH fires, confirm the fan is actually running (LINE1.FAN_01.STOPPED = false) before checking for a blocked intake filter, a stopped fan is the most common cause and is a faster fix than a filter change.

¶4. Preheater Temperature High Response
If LINE1.HEATER_01.TEMP_HIGH fires, do not manually cycle the heater breaker, use the HMI setpoint reduction first and allow the control loop to bring it down. Manual breaker cycling has caused nuisance trips on this line in the past.

¶5. Escalation
If either temperature does not trend down within 5 minutes of corrective action, escalate to maintenance before the associated high-high safety interlock trips the line.
