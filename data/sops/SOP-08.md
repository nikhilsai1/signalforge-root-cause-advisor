# SOP-08: Pump Flow Deviation Response

**Applies to:** LINE1.PUMP_01, LINE1.PUMP_02, LINE1.PUMP_03
**Monitored tags:** LINE1.PUMP_01.FLOW_LOW, LINE1.PUMP_01.FLOW_HIGH, LINE1.PUMP_02.FLOW_LOW

¶1. Purpose
Covers operator response to low or high flow alarms on feed and discharge pumps.

¶2. Monitored Tags
- LINE1.PUMP_xx.FLOW_LOW: measured flow below setpoint band
- LINE1.PUMP_xx.FLOW_HIGH: measured flow above setpoint band

¶3. Low Flow Response
If LINE1.PUMP_xx.FLOW_LOW fires while the pump is running, check upstream tank level (SOP-09) before assuming pump failure, a low-level condition upstream is a more frequent cause than pump wear. If upstream level is normal, check for a partially closed valve (SOP-10) on the suction line.

¶4. High Flow Response
If LINE1.PUMP_xx.FLOW_HIGH fires, check downstream valve position first, a stuck-open or fully-open discharge valve is the most common cause. Do not throttle the pump speed directly without confirming valve state.

¶5. Escalation
If flow does not return to the setpoint band within 5 minutes of corrective action, stop the pump and escalate to maintenance, continued running outside the flow band risks cavitation damage.
