// Placeholder data only — no backend wiring yet. Shapes match the real
// alarm_flood.json / SOP schema already established for the project, so
// swapping this for a live fetch later should be a drop-in change.

export const alarms = [
  {
    id: 1,
    tag: "LINE1.MTR_01.OVERLOAD",
    description: "Motor_1 overload trip",
    priority: "critical",
    timestamp: "14:32:00",
    isRootCause: true,
    clusteredCount: 42,
  },
  {
    id: 2,
    tag: "LINE1.SENS_02.COMM_LOSS",
    description: "Flow sensor 2 communication loss",
    priority: "medium",
    timestamp: "14:08:12",
  },
  {
    id: 3,
    tag: "LINE1.TANK_02.LEVEL_LOW",
    description: "Surge tank 2 level low",
    priority: "low",
    timestamp: "13:52:40",
  },
  {
    id: 4,
    tag: "LINE1.VLV_03.POSITION_FAULT",
    description: "Drain valve position feedback fault",
    priority: "low",
    timestamp: "13:41:05",
  },
  {
    id: 5,
    tag: "LINE1.FAN_01.TEMP_HIGH",
    description: "Cooling fan intake temperature high",
    priority: "medium",
    timestamp: "13:15:52",
  },
  {
    id: 6,
    tag: "LINE1.PUMP_02.FLOW_LOW",
    description: "Feed pump 2 flow below setpoint",
    priority: "high",
    timestamp: "12:58:19",
  },
];

// Keyed by alarm id — the guidance the copilot would generate for that alarm.
export const guidanceByAlarmId = {
  1: {
    rootCause: "Motor_1 overload trip (LINE1.MTR_01.OVERLOAD)",
    fix: "Check for a jammed or stalled conveyor downstream before resetting the drive. Confirm load reads normal at zero speed, then reset from the HMI with a ramped start, not direct-on-line.",
    citation: "SOP-14 §3 — VFD Overload Response",
    cited: true,
  },
  2: {
    rootCause: "Flow sensor 2 lost network communication",
    fix: "Check the local junction box connection before escalating to network diagnostics. Switch the loop to manual if not restored within 5 minutes.",
    citation: "SOP-11 §3 — Immediate Response",
    cited: true,
  },
  3: {
    rootCause: "Surge tank 2 level trending low",
    fix: "Check the upstream feed pump and conveyor for a stoppage before assuming a leak.",
    citation: "SOP-09 §4 — Low Level Response",
    cited: true,
  },
  4: {
    rootCause: "Drain valve feedback deviates from commanded position",
    fix: "Check instrument air supply pressure at the local panel before assuming an actuator failure.",
    citation: "SOP-10 §3 — Fault Response",
    cited: true,
  },
  5: {
    rootCause: "Cooling fan intake temperature above 45C",
    fix: "Confirm the fan is running before checking for a blocked intake filter.",
    citation: "SOP-12 §3 — Fan Temperature High Response",
    cited: true,
  },
  6: {
    rootCause: "Feed pump 2 flow below setpoint",
    fix: "Check upstream tank level before assuming pump wear. If level is normal, check for a partially closed suction valve.",
    citation: "SOP-08 §3 — Low Flow Response",
    cited: true,
  },
};

export const initialChatLog = [
  {
    role: "operator",
    text: "Why did Motor_1 trip and what do I do?",
  },
  {
    role: "copilot",
    text: "Motor_1 tripped on overload. 42 related alarms clustered under this one root cause, not separate issues. Check SOP-14 §3 before resetting, likely a downstream conveyor jam.",
  },
];
