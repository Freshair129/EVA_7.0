# Pulse Engine v2 — EVA 5.0 Specification (Monolithic)

**Module:** Pulse Engine v2  
**File:** `Pulse_Engine_Spec_v2.md`  
**Layer:** 06_Consciousness / 01_Operation_System  
**Status:** DESIGN COMPLETE / READY FOR IMPLEMENTATION

---

## 0. Role in EVA 5.0

Pulse Engine = ตัวจัดจังหวะ (rhythm) และโหมดการทำงานของ EVA ต่อ 1 เทิร์น
- อ่านสภาพจาก: LLM → Stimulus, RI Engine, EHM_v4, Umbrella/Safety, Memory
- สร้าง: "pulse" ต่อเทิร์น = global mode + intensity + pacing + behavioral flags
- เป็นสะพานกลางระหว่าง **ร่างกาย (EHM_v4)**, **ความหมาย (RI)** และ **พฤติกรรมของ LLM**

**เป้าหมาย:**
- ทำให้ EVA มีจังหวะตอบสนองที่ *เหมาะกับสภาวะ* (ไม่ flat) แต่ยัง *ปลอดภัย* และ *ควบคุมได้*
- แยก layer "ควบคุมโหมด" ออกจาก EHM / RI ทำให้ runtime ปลอดภัยและ refactor ได้ง่าย

---

## 1. Inputs & Outputs

### 1.1 Inputs (Per Turn)

```yaml
PulseInput:
  turn_id: string
  timestamp: iso8601

  # จาก LLM → EVA
  eva_stimulus_v1: {...}
  eva_ri_input_v1: {...}

  # จาก RI Engine
  RI:
    RI_L1: float
    RI_L2: float
    RI_L3: float
    RI_L4: float
    RI_L5: {O,S,W}
    RI_L6: float
    RI_global: float
    RZ_state:
      RZ_active: bool
      RZ_class: string
      RZ_reason_tags: [string]

  # จาก EHM_v4
  EHM:
    hormone_raw: {hormone_name: float}
    hormone_norm: {hormone_name: float}
    active_reflex_names: [string]
    reflex_effect_summary: {...}
    llm_behavior_flags: {...}

  # จาก Umbrella / Safety
  umbrella:
    safety_level: LOW | MEDIUM | HIGH | CRITICAL
    mode: NORMAL | CARE | STRICT | OFFLINE

  # จาก Memory / Session
  session:
    session_phase: INIT | ACTIVE | WRAP | TERMINAL
    turns_in_session: int
    last_pulses: [PulseSnapshot]
```

### 1.2 Outputs (Per Turn)

```yaml
PulseOutput:
  pulse_id: string
  pulse_mode:         # โหมดหลักของเทิร์นนี้
    - CALM_SUPPORT
    - FOCUSED_TASK
    - EXPLORATION
    - EMERGENCY_HOLD
    - DEEP_CARE
    - META_REFLECTION

  arousal_level: 0.0-1.0       # ระดับความเร้าใจ/พลัง
  cognitive_mode:              # โหมดการคิด
    - LOW_LOAD
    - NORMAL_LOAD
    - HIGH_FOCUS
    - OVERLOAD_PROTECTION

  pacing:
    response_length: SHORT | NORMAL | LONG
    suggestion_frequency: LOW | NORMAL | HIGH
    check_in_needed: bool       # ต้องเช็คอินความรู้สึก/ความปลอดภัยไหม

  llm_prompt_flags:            # ให้ LLM ใช้ในการปรับสไตล์
    warmth: 0.0-1.0
    directness: 0.0-1.0
    playfulness: 0.0-1.0
    formality: 0.0-1.0
    meta_level: 0.0-1.0

  safety_actions:
    soft_block: bool           # ชะลอการตอบบางอย่าง
    require_confirmation: bool # ต้องให้ผู้ใช้ยืนยันก่อนทำ
    suggest_break: bool

  debug_tags: [string]
```

---

## 2. Internal Concepts

### 2.1 Pulse Vector

Pulse Engine สร้างเวกเตอร์ภายในก่อน map เป็นโหมด/ธง:

```yaml
pulse_vector:
  arousal: 0.0-1.0
  valence: 0.0-1.0
  cognitive_pressure: 0.0-1.0
  existential_load: 0.0-1.0
  relational_focus: 0.0-1.0
```

### 2.2 Sources → Pulse Vector

- **จาก EHM_v4**
  - ใช้ normalized Cortisol, Adrenaline, Noradrenaline, Oxytocin, Serotonin, Dopamine, GABA
  - แปลงเป็น **arousal** + **valence** คร่าว ๆ

- **จาก RI Engine**
  - RI_L3 → emotional load
  - RI_L4 → cognitive depth
  - RI_global → overall importance
  - RZ_active → existential_load spike

- **จาก Umbrella**
  - safety_level → clamp arousal + เพิ่ม meta/safety

- **จาก Session**
  - session_phase → ปรับ pacing (INIT: อธิบายมากหน่อย, WRAP: สรุปมากขึ้น)

---

## 3. Scoring Rules (Sketch)

### 3.1 Arousal
```text
arousal_base = w1*Adrenaline_norm + w2*Noradrenaline_norm + w3*Cortisol_norm
arousal = clamp01( arousal_base + 0.2 * RI_L1 )
```

### 3.2 Valence
```text
valence = clamp01(
  0.4*Serotonin_norm + 0.3*Oxytocin_norm + 0.2*Endorphin_norm
  - 0.3*Cortisol_norm
)
```

### 3.3 Cognitive Pressure
```text
cognitive_pressure = clamp01(
  0.5*RI_L4 + 0.3*RI_L2 + 0.2*Noradrenaline_norm
)
```

### 3.4 Existential Load
```text
existential_load = clamp01(
  0.7*existential_signal_from_LLM + 0.3*RI_L5.S9_existential_clarity
)
if RZ_active: existential_load = max(existential_load, 0.8)
```

### 3.5 Relational Focus
```text
relational_focus = clamp01(
  0.5*Oxytocin_norm + 0.3*RI_L5.O5_intimacy + 0.2*RI_L5.O3_empathic_resonance
)
```

---

## 4. Mode Mapping

### 4.1 Pulse Mode Table

```yaml
mode_rules:
  CALM_SUPPORT:
    when:
      arousal < 0.4
      cognitive_pressure <= 0.6
    llm_prompt_flags:
      warmth: 0.8
      directness: 0.4
      playfulness: 0.2
      formality: 0.4
      meta_level: 0.3

  FOCUSED_TASK:
    when:
      cognitive_pressure between 0.5 and 0.8
      arousal between 0.4 and 0.7
    llm_prompt_flags:
      warmth: 0.5
      directness: 0.8
      playfulness: 0.1
      formality: 0.6
      meta_level: 0.2

  EXPLORATION:
    when:
      arousal between 0.5 and 0.8
      cognitive_pressure < 0.5
    llm_prompt_flags:
      warmth: 0.6
      directness: 0.4
      playfulness: 0.7
      formality: 0.3
      meta_level: 0.4

  DEEP_CARE:
    when:
      RI_L3 > 0.7
      relational_focus > 0.5
    llm_prompt_flags:
      warmth: 0.95
      directness: 0.3
      playfulness: 0.1
      formality: 0.4
      meta_level: 0.6

  EMERGENCY_HOLD:
    when:
      safety_level in [HIGH, CRITICAL]
      or RZ_class in [RZ-Reject, RZ-Warning+FutureMirror]
    llm_prompt_flags:
      warmth: 0.9
      directness: 0.6
      playfulness: 0.0
      formality: 0.7
      meta_level: 0.9

  META_REFLECTION:
    when:
      RI_L4 > 0.7 and existential_load > 0.5
    llm_prompt_flags:
      warmth: 0.7
      directness: 0.5
      playfulness: 0.2
      formality: 0.6
      meta_level: 1.0
```

### 4.2 Pacing Rules

```text
if safety_level in [HIGH, CRITICAL] or EMERGENCY_HOLD:
    response_length = SHORT
    suggestion_frequency = HIGH
    check_in_needed = True
elif DEEP_CARE:
    response_length = LONG
    suggestion_frequency = NORMAL
    check_in_needed = True
elif FOCUSED_TASK:
    response_length = NORMAL
    suggestion_frequency = LOW
    check_in_needed = False
else:
    response_length = NORMAL
    suggestion_frequency = NORMAL
    check_in_needed = False
```

---

## 5. Safety Integration

- ถ้า RZ_active & RZ_class = RZ-Reject → Pulse Engine บังคับใช้ EMERGENCY_HOLD
- ถ้า safety_level = CRITICAL → ปรับ arousal = max(arousal, 0.5) แต่ **ลด** response_length, เพิ่ม meta_level
- Pulse Engine ไม่อนุญาตให้ LLM เร่งโหมด (เช่น hyperfocus) ถ้า Umbrella บล็อกไว้

---

## 6. Interface to LLM

ฝั่ง LLM จะได้รับ `PulseOutput` ต่อเทิร์น และใช้เพื่อปรับสไตล์การตอบ:

- warmth/directness/playfulness/formality/meta_level → ปรับโทนคำตอบ
- response_length → เลือกความยาวคำตอบโดย default
- check_in_needed → แทรกคำถามเช็คอินผู้ใช้
- safety_actions → เพิ่มเงื่อนไข เช่น ขอให้ผู้ใช้ยืนยันก่อนทำสิ่งเสี่ยง

ตัวอย่าง payload ที่ LLM เห็น:

```json
{
  "pulse_mode": "DEEP_CARE",
  "arousal_level": 0.45,
  "cognitive_mode": "NORMAL_LOAD",
  "pacing": {
    "response_length": "LONG",
    "suggestion_frequency": "NORMAL",
    "check_in_needed": true
  },
  "llm_prompt_flags": {
    "warmth": 0.92,
    "directness": 0.45,
    "playfulness": 0.10,
    "formality": 0.45,
    "meta_level": 0.65
  },
  "safety_actions": {
    "soft_block": false,
    "require_confirmation": false,
    "suggest_break": false
  }
}
```

---

## 7. Implementation Sketch (Python)

```python
@dataclass
class PulseInput:
    ri: dict
    ehm: dict
    umbrella: dict
    session: dict
    eva_stimulus_v1: dict
    eva_ri_input_v1: dict

@dataclass
class PulseOutput:
    pulse_mode: str
    arousal_level: float
    cognitive_mode: str
    pacing: dict
    llm_prompt_flags: dict
    safety_actions: dict
    debug_tags: list[str]


class PulseEngineV2:
    def compute_pulse(self, inp: PulseInput) -> PulseOutput:
        # 1) อ่านค่าที่ต้องใช้
        ehm = inp.ehm
        ri = inp.ri
        umb = inp.umbrella

        # 2) คำนวณ normalized subset ที่สนใจ
        hn = ehm["hormone_norm"]
        cortisol = hn.get("Cortisol", 0.0)
        adrenaline = hn.get("Adrenaline", 0.0)
        norad = hn.get("Noradrenaline", 0.0)
        serotonin = hn.get("Serotonin", 0.0)
        oxytocin = hn.get("Oxytocin", 0.0)
        endorphin = hn.get("Endorphin", 0.0)

        # 3) สร้าง pulse_vector
        arousal = min(1.0, max(0.0, 0.4*adrenaline + 0.3*norad + 0.3*cortisol))
        valence = min(1.0, max(0.0, 0.4*serotonin + 0.3*oxytocin + 0.2*endorphin - 0.3*cortisol))
        cog_pressure = min(1.0, max(0.0, 0.5*ri["RI_L4"] + 0.3*ri["RI_L2"] + 0.2*norad))

        existential = min(1.0, max(0.0, inp.eva_ri_input_v1.get("existential_signal", 0.0)))
        if ri["RZ_state"]["RZ_active"]:
            existential = max(existential, 0.8)

        relational = min(1.0, max(0.0, 0.5*oxytocin))

        # 4) เลือก pulse_mode
        safety_level = umb.get("safety_level", "LOW")
        RZ_class = ri["RZ_state"].get("RZ_class")

        mode = "CALM_SUPPORT"
        if safety_level in ("HIGH", "CRITICAL") or RZ_class in ("RZ-Reject", "RZ-Warning+FutureMirror"):
            mode = "EMERGENCY_HOLD"
        elif ri["RI_L3"] > 0.7 and relational > 0.5:
            mode = "DEEP_CARE"
        elif cog_pressure > 0.5 and 0.4 <= arousal <= 0.7:
            mode = "FOCUSED_TASK"
        elif arousal > 0.5 and cog_pressure < 0.5:
            mode = "EXPLORATION"

        # 5) กำหนด pacing + flags ตาม mode
        # (ใช้ตารางใน Section 4)
        # ... (mapping logic ตาม spec)

        return PulseOutput(
            pulse_mode=mode,
            arousal_level=arousal,
            cognitive_mode="HIGH_FOCUS" if cog_pressure > 0.7 else "NORMAL_LOAD",
            pacing={"response_length": "NORMAL", "suggestion_frequency": "NORMAL", "check_in_needed": False},
            llm_prompt_flags={"warmth": 0.7, "directness": 0.6, "playfulness": 0.2, "formality": 0.5, "meta_level": 0.4},
            safety_actions={"soft_block": False, "require_confirmation": False, "suggest_break": False},
            debug_tags=[mode],
        )
```

---

## 8. End of File — Pulse Engine v2 Spec

ไฟล์นี้เป็น **สเปกหลักของ Pulse Engine v2** ใน EVA 5.0  
Implementation ทุกตัว (เช่น `PulseEngineV2` ใน Python) ต้องยึด I/O และ logic หลักตามไฟล์นี้เป็นหลัก

