# SOP-13: Alarm Flood & Cascade Handling

**Applies to:** Line 1, all equipment
**Reference standard:** ISA-18.2, alarm flood defined as more than 10 alarms in any rolling 10-minute window

¶1. Purpose
Covers operator response when the alarm list fills faster than individual alarms can be triaged one at a time.

¶2. Recognizing a Flood
If more than 10 alarms arrive within 10 minutes, treat this as a flood condition per ISA-18.2, not as 10+ separate problems. Do not attempt to acknowledge and investigate each alarm individually in real time during a flood.

¶3. Root-Cause-First Response
During a flood, identify the earliest-timestamped alarm in the cluster before responding to any later alarm, in most cases on this line the first alarm is the root cause and the rest are consequences of it, not independent failures. Cross-check the earliest alarm's equipment tag against the relevant equipment SOP (SOP-07 through SOP-12) rather than the SOPs for the later, downstream alarms.

¶4. Acknowledgment Discipline
Acknowledge the root alarm first. Downstream alarms that clear on their own once the root cause is fixed do not each need individual root-cause investigation.

¶5. Escalation
Any flood that does not resolve within 10 minutes of addressing the identified root cause should be escalated to a shift supervisor.
