# SOP-11: Sensor Communication Loss Response

**Applies to:** LINE1.SENS_01, LINE1.SENS_02, LINE1.SENS_03
**Monitored tags:** LINE1.SENS_01.COMM_LOSS, LINE1.SENS_02.COMM_LOSS

¶1. Purpose
Covers operator response when a field sensor drops off the Modbus or MQTT network and stops reporting.

¶2. Monitored Tags
- LINE1.SENS_xx.COMM_LOSS: set after 3 missed poll cycles

¶3. Immediate Response
If LINE1.SENS_xx.COMM_LOSS fires, do not assume the underlying process value, treat it as unknown, not as the last good reading. Check the local junction box connection before escalating to network diagnostics. Most comm losses on this line are a loose terminal, not a network fault.

¶4. Operating Without the Sensor
If the sensor cannot be restored within 5 minutes, switch the associated loop to manual and rely on the nearest redundant or downstream sensor if one exists. Log the substitution in the shift log so the next operator knows a sensor is out.

¶5. Escalation
Any comm loss lasting more than 20 minutes should be escalated to the network/OT team, not left as a standing condition across a shift change.
