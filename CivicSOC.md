# CivicSOC

## AI Safety & Resilience Operations Centre for Dublin

### One-Line Pitch

**CivicSOC uses AI and public infrastructure data to detect early warning signals, prevent incidents from escalating, protect public infrastructure, and help operators respond faster when something goes wrong.**

---

# The Problem

Cities generate enormous amounts of infrastructure data.

Traffic sensors measure speed and flow. Weather stations monitor road conditions. Road closure systems track disruptions. Transport systems monitor movement. CCTV and traffic infrastructure provide visibility across the city.

But these signals are fragmented.

When something starts going wrong, operators often need to manually piece together information from different systems to understand:

- Is this behaviour normal?
- Is an incident developing?
- Is there an accident or dangerous road condition?
- Is a planned closure causing the disruption?
- Could weather be contributing?
- Which infrastructure is affected?
- How serious could the situation become?
- Where should operators intervene first?

The challenge is not a lack of data.

**The challenge is turning fragmented data into an early warning system.**

---

# The Vision

## Protect lives and public infrastructure by detecting problems before they become disasters.

CivicSOC is an AI-powered safety and resilience layer for cities.

It continuously monitors infrastructure signals, identifies abnormal behaviour, correlates different sources of information, predicts how problems could develop, and helps human operators intervene.

The system is designed around one principle:

> **Don't wait for an incident to become obvious. Detect the signals that something is going wrong and act earlier.**

---

# The Solution

CivicSOC transforms public infrastructure data into a live operational safety network.

When the system detects an abnormal situation, it:

1. **Detects** unusual behaviour
2. **Correlates** multiple data sources
3. **Assesses** potential causes and risk
4. **Identifies** affected infrastructure
5. **Predicts** how the situation could escalate
6. **Alerts** the appropriate operator
7. **Recommends** possible interventions
8. **Simulates** the expected outcome

The AI does not replace emergency or infrastructure operators.

It gives them **earlier awareness and better information for decision-making.**

---

# MVP: Dublin Transport Safety

The first version focuses on **Dublin's transport network**.

This gives CivicSOC a concrete environment where public data can be used to demonstrate the larger vision.

### The MVP monitors:

- Road traffic
- Vehicle speeds
- Traffic flow
- Travel times
- Road closures
- Weather conditions
- Traffic signal locations
- CCTV infrastructure locations
- Other relevant public mobility data

The goal is not simply to create another traffic dashboard.

The goal is to detect **potentially dangerous or disruptive situations early.**

---

# The Core Experience

The interface is **map-first**.

The map is the product.

Instead of forcing operators to read dashboards full of charts, CivicSOC communicates the state of the city visually.

### LIVE CITY → EARLY WARNING → INVESTIGATION → PREDICTION → INTERVENTION

---

# 1. LIVE

The system continuously visualises Dublin's transport network.

Roads are displayed according to their current state.

```text
GREEN
Normal conditions

AMBER
Emerging anomaly / elevated risk

RED
Active disruption / high priority

PULSING RED
Critical incident requiring investigation
```

Traffic movement is animated across the road network.

Infrastructure locations appear as contextual layers.

The operator can immediately understand what is happening without reading multiple dashboards.

---

# 2. DETECT

CivicSOC establishes what normal conditions look like and looks for significant deviations.

Example:

```text
Travel time       +81%
Average speed     -47%
Traffic volume    +21%

Road closure      NONE
Severe weather    NONE

                    ↓

          SIGNIFICANT ANOMALY
```

The affected corridor transitions:

```text
GREEN → AMBER → RED
```

A pulsing incident marker appears.

The system has identified something that deserves attention.

---

# 3. IDENTIFY POTENTIAL RISK

An anomaly does not automatically mean an accident.

CivicSOC checks multiple signals to determine what could explain the behaviour.

Example:

```text
TRAFFIC ANOMALY       ✓
PLANNED ROAD CLOSURE  ✕
SEVERE WEATHER        ✕
KNOWN EVENT           ?
INFRASTRUCTURE NEARBY ✓
```

The system can then classify the situation as:

```text
NORMAL
    ↓
UNUSUAL
    ↓
POTENTIAL INCIDENT
    ↓
HIGH-RISK EVENT
```

This distinction is important.

CivicSOC is designed to **surface risk early**, not falsely claim certainty.

---

# 4. PROTECT LIVES

The ultimate purpose of early detection is intervention.

For example, CivicSOC could identify a combination of:

- abnormal traffic behaviour
- rapidly changing speeds
- unusual congestion
- adverse weather
- road-network conditions

and raise an early warning:

```text
┌─────────────────────────────┐
│     POTENTIAL INCIDENT      │
│                             │
│     Risk: HIGH              │
│     Location: R132          │
│                             │
│  Immediate investigation    │
│  recommended                │
└─────────────────────────────┘
```

The system does not claim:

> "An accident will definitely happen."

Instead:

> **"Conditions indicate elevated incident risk. Investigate now."**

That is a much more realistic and defensible safety application.

---

# 5. VERIFY

When an anomaly is detected, CivicSOC identifies relevant infrastructure nearby.

For example:

```text
                    🔴
                 ANOMALY
                    │
                    │ 420m
                    │
                    ▼
                    📹
                   CCTV
```

The map can animate the connection between the detected event and nearby infrastructure.

If a permitted live camera feed is available, it can provide additional verification.

If no live feed is available, CivicSOC still tells an operator:

> **Nearest verification infrastructure: CCTV — 420m**

This turns infrastructure data into an actionable investigation tool.

---

# 6. PREDICT

CivicSOC estimates how an incident or disruption could affect the surrounding network.

The map becomes a visual simulation.

### CURRENT

```text
       🟢
──────────────
       🔴
──────────────
       🟢
```

### +5 MINUTES

```text
       🟠
───────🔴───────
       🟠
```

### +15 MINUTES

```text
    🟠  🟠
────🟠 🔴 🟠────
    🟠  🟠
```

The operator can see the potential spread of the disruption rather than interpreting a static number.

---

# 7. INTERVENE

CivicSOC can recommend an operational response.

Example:

```text
RECOMMENDED RESPONSE

Divert traffic through R132

Predicted