# SOP-14: Motor & VFD Fault Response

**Applies to:** LINE1.MTR_01, LINE1.MTR_02, LINE1.VFD_01, LINE1.VFD_02
**Monitored tags:** LINE1.MTR_01.OVERLOAD, LINE1.VFD_01.CURRENT_HIGH, motor_load_pct

¶1. Purpose
Covers operator response to motor and variable frequency drive (VFD) fault conditions, including overload trips.

¶2. Monitored Tags
- LINE1.MTR_xx.OVERLOAD: motor overload trip flag
- LINE1.VFD_xx.CURRENT_HIGH: drive current draw above rated threshold
- motor_load_pct: continuous drive load, percent of rated capacity (process data feed)

¶3. VFD Overload Response
If LINE1.MTR_xx.OVERLOAD fires and motor_load_pct was trending above 90% prior to trip, this is an overload trip, not an electrical fault. Do not reset the drive immediately. First check for a mechanical cause downstream, a jammed or stalled conveyor (SOP-07) is the most common root cause of motor overload on this line. Clear the mechanical cause, confirm motor_load_pct reads normal at zero speed, then reset the drive from the HMI and bring the motor back up on a ramped start, not a direct-on-line restart.

¶4. Electrical Fault Response
If LINE1.VFD_xx.CURRENT_HIGH fires but motor_load_pct was normal prior to trip (no overload trend), treat this as a potential electrical fault rather than a mechanical overload. Do not reset more than once. Escalate to electrical maintenance before a second reset attempt.

¶5. Escalation
Any motor that trips on overload twice in the same shift should be escalated to maintenance for a mechanical inspection before further resets are attempted, repeated resets without addressing the downstream cause risk drive damage.
