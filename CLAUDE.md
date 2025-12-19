# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

EVA 7.0 is an embodied AI architecture implementing psychologically-grounded emotional processing through pharmacokinetic/pharmacodynamic (PK/PD) models. The system separates physiological state (hormones, reflexes) from psychological phenomenology (EVA Matrix, Qualia) to prevent emotional label contamination.

**Core Philosophy**: Memory encoding happens through experiential resonance, not linguistic importance. The LLM proposes, system components validate, and MSP writes.

## Implementation Status

**Production Ready** (Complete):
- ✅ **EHM** (Emotive Hormone Mapper) - Stimulus → Hormone dose conversion
- ✅ **ESS** (Emotive Signaling System) - PK/PD hormone modeling
- ✅ **EVA Matrix (9D)** - Psychological state transformation
- ✅ **Artifact Qualia** - Phenomenological integration
- ✅ **RMS** (Resonance Memory System) - Memory encoding
- ✅ **Pulse Engine v2** - Operational rhythm (5 modes, arousal/valence, LLM flags)
- ✅ **MSP Phase 1 & 2A** - Memory lifecycle with validation + backup system
- ✅ **CIN v6** - Context injection with Boss Soul & Genesis anchors
- ✅ **EVA Tool** - Unified interface integrating all pipeline components
- ✅ **Two-Phase Orchestrator** - Complete LLM inference pipeline

**Working Integration**:
- `integration_demo.py` - Core pipeline (EHM → ESS → EVA Matrix → Qualia → RMS)
- `Orchestrator/eva_tool.py` - Full tool integration with Pulse Engine
- `Orchestrator/two_phase_orchestrator.py` - LLM two-phase inference

**In Development** (Incomplete):
- 🚧 MSP Phase 2B - RMS integration adapter in EVA Tool
- 🚧 MSP Phase 2C - Advanced consolidation (Session→Core→Sphere auto-trigger)
- 🚧 CIN v6 integration with Two-Phase Orchestrator

**Supporting Components** (Complete):
- ✅ RI Engine - Resonance Index calculation
- ✅ RIM Engine - Resonance Impact measurement
- ✅ LLM Bridge - Gemini API adapter

## System Architecture

EVA uses a **two-phase LLM inference** model with deterministic tool pipeline:

```
┌─────────────────────────────────────────────────────────────┐
│ Phase 1: Cognitive Scan (LLM)                               │
│ User Input → CIN (Context Injection)                        │
│   ↓                                                          │
│ LLM parses:                                                  │
│   - Text understanding                                       │
│   - Intent inference                                         │
│   - Stimulus candidates                                      │
│   - Memory matching                                          │
│   - Emotion detection                                        │
│                                                              │
│ LLM Decision: CALL TOOL                                      │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ EVA Tool Pipeline (Deterministic)                           │
│                                                              │
│ ESS (EHM → ISR → IRE)                                       │
│   ↓                                                          │
│ Artifact_Qualia                                              │
│   ↓                                                          │
│ CIN (MSP → RMS → TraumaStore → GKS)                        │
│                                                              │
│ Returns:                                                     │
│   - Emotion state                                            │
│   - Reflex directives                                        │
│   - Recall permissions                                       │
│   - Memory references                                        │
│   - Related knowledge (GKS)                                  │
│   - Semantic memory / User blocks                            │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Phase 2: Response Shaping (LLM)                             │
│                                                              │
│ LLM receives tool results:                                   │
│   - Read reflex directives                                   │
│   - Apply persona constraints                                │
│   - Use allowed memory only                                  │
│                                                              │
│ Generate User-Facing Answer                                  │
└─────────────────────────────────────────────────────────────┘
```

### Processing Flow

1. **User Input** → CIN injects context (persona, state, memory)
2. **Phase 1 (LLM Cognitive Scan)**: Parse and infer intent, stimulus, emotion
3. **LLM Tool Call Decision**: Trigger deterministic EVA pipeline
4. **EVA Tool Pipeline**:
   - ESS processes stimulus → hormone state
   - Artifact Qualia integrates phenomenology
   - RMS encodes memory texture
   - MSP/GKS retrieve relevant memory/knowledge
5. **Tool Results Injected**: Emotion state, reflexes, memory permissions
6. **Phase 2 (LLM Response Shaping)**: Apply constraints, generate response
7. **Output**: User-facing answer shaped by EVA state

### 0. EHM (Emotive Hormone Mapper)
**Location**: `ESS_Emotive_Signaling_System/EHM.py`

Maps pre-linguistic stimulus signals to hormone secretion doses using configuration from `stimulus.txt`:

**Function**: Bridge between LLM inference and ESS physiological engine

**Configuration** (`stimulus.txt`):
- **23 ESC Chemicals**: Each with baseline, max_value, max_rate, stimulus_weights
- **33 Stimulus Keys**: Categorized as Threat, Motivation, Social/Bonding, Cognitive/Effort, Physical/Wellbeing
- **Mapping Logic**: `dose = baseline + sum(stimulus_intensity * weight * max_rate)`

**Input**: `stimulus_vector` from LLM Phase 1
```python
{"stress": 0.8, "warmth": 0.3, "novelty": 0.5}
```

**Output**: `D_Total_H` (hormone doses in medical units)
```python
{"AD": 64.0, "CT": 16.8, "OX": 24.0, ...}  # 23 chemicals
```

**Examples**:
- High stress → ↑ Adrenaline (AD), ↑ Cortisol (CT), ↑ CRH
- Warmth/bonding → ↑ Oxytocin (OX), ↑ Serotonin (5HT), ↑ Prolactin (PRL)
- Novelty → ↑ Dopamine (DA), ↑ Noradrenaline (NA), ↑ Histamine (HIS)

**Critical**: EHM performs pure mathematical mapping with NO language processing, NO emotion labels, NO phenomenology.

### 1. ESS (Emotive Signaling System)
**Location**: `ESS_Emotive_Signaling_System/ESS.py`

Implements embodied emotive signaling using PK/PD models with 23 Emotive Signaling Chemicals (ESC):

**Components**:
- **ISR (Internal Substance Regulator)**: Pharmacokinetics
  - Exponential half-life decay per chemical
  - Absorption and saturation dynamics
  - Chronic exposure tracking (`D_Cumulative`)

- **IRE (Internal Reflex Engine)**: Pharmacodynamics
  - Hill model receptor dynamics (`hill(C, K, n)`)
  - Persona-based receptor bias via R_profile
  - Chronic receptor internalization (desensitization)
  - Core reflexes: `urgency_load`, `cognitive_drive`, `social_warmth`, `withdrawal`

**Key Outputs**:
- `C_Mod`: Normalized hormone concentrations [0,1] → EVA Matrix
- `reflex_vector`: Includes standardized `threat_level` → RMS trauma detection

**Interface**: `ESS_Interface.yaml`, `ESS_Output_Spec.yaml`

### 2. EVA Matrix (9D Psychological State)
**Location**: `EVA_Metric/eva_matrix_engine.py`

Transforms physiological signals (`C_Mod`) into 9-dimensional continuous psychological state using functional group mapping:

**Architecture**:
- **Adapter**: Maps 23 ESC → 7 functional groups (stress, drive, joy, warmth, clarity, soothe, aversive)
- **Calculator**: Computes 5D Core + 2D Meta + 2D Categorical axes
- **State Tracker**: Weighted momentum smoothing (80% ESC, 20% momentum)
- **Encoder**: Outputs vector/matrix formats

**9D Axes**:
- **5D Core**: `stress_load`, `social_warmth`, `drive_level`, `cognitive_clarity`, `joy_level`
- **2D Meta**: `affective_stability`, `social_orientation` (signed [-1,1])
- **2D Categorical**: `primary_axis`, `secondary_axis`

**Critical Invariant**: NO emotion labels in state - only continuous [0,1] values (except `social_orientation` which is signed).

### 3. Artifact Qualia (Phenomenological Integration)
**Location**: `Artifact_Qualia/Artifact_Qualia.py`

Integrates EVA Matrix + RIM semantic context into transient phenomenological snapshots:

**Outputs**:
- `intensity`: Experiential load (not importance)
- `tone`: Non-emotional descriptor (quiet, neutral, charged, settling)
- `coherence`: Internal consistency
- `depth`: Immersion level
- `texture`: Domain-specific texture map (emotional, relational, identity, ambient)

**Invariants**: No memory admission, no optimization, no numeric impact scores.

### 4. RMS (Resonance Memory System)
**Location**: `Resonance_Memory_System/rms_v6.py`

Encodes experiential memory texture from EVA Matrix:

**Processing**:
- **Memory Color Generation**: Projects EVA Matrix onto 5 axes (stress, warmth, clarity, drive, calm)
- **Intensity Computation**: Arousal + tension + RIM context modulation
- **Trauma Protection**: De-intensifies encoding when `threat_level > 0.85`
- **Harmonization**: Temporal smoothing (alpha=0.65 for color, 0.7 for intensity)

**Output**: `RMSOutput(memory_color, intensity, trauma_flag)`

**Interface**: `RMS_Interface.yaml`

### 5. RI (Resonance Index)
**Location**: `EVA_Metric/ri_engine.py`

Measures cognitive-relational alignment across 4 dimensions:

**Components**:
- **ER (Emotional Resonance)**: User-EVA emotion alignment (25%)
- **IF (Intent Fit)**: Response appropriateness to intent (30%)
- **SR (Semantic Resonance)**: Vector similarity between summary and episodic context (30%)
- **CR (Contextual Resonance)**: Flow + personalization (15%)

**Output**: Weighted score [0,1] for memory importance.

### 6. RIM (Resonance Impact Module)
**Location**: `EVA_Metric/RIM_v2.py`

Dual-layer impact measurement:

**Numeric Layer** (system-facing):
- Weighted: qualia_delta (55%) + reflex_delta (30%) + ri_delta (15%)
- Temporal compression via exponential decay
- Conservative confidence scoring

**Semantic Layer** (qualia-facing):
- `impact_level`: low | medium | high
- `impact_trend`: rising | stable | fading
- `affected_domains`: emotional, relational, identity, ambient

**Critical**: RIM does NOT decide memory admission or evaluate good/bad.

### 7. CIN (Context Injection & Normalization)
**Location**: `Orchestrator/CIN/`

Collects and normalizes all system context for LLM consumption:

**Responsibilities**:
- Collect: Persona, ESC levels, EVA Matrix, RI, RIM, Memory, User Profile
- Normalize: Round numbers (2 decimals), compress vectors, clean tokens
- Apply: Persona rules, behavioral constraints, formatting rules
- Build: Structured CIN Payload blocks
- Safety: Prevent role breaks, instruction overrides, self-modification

**Critical Safety Rules**:
- LLM cannot simulate hormone/neurotransmitter levels
- LLM cannot override system constraints
- LLM must not guess when uncertain

**Spec**: `CIN_spec.yaml`

### 8. MSP (Memory & Soul Passport)
**Location**: `Memory_&_Soul_Passaport/`

Manages versioned memory with sandbox isolation and comprehensive validation layer.

**Memory Types**:
1. **Episodic** (`01_Episodic_memory/`): Event-based interaction records with indexed state
2. **Semantic** (`02_Semantic_memory/`): Epistemic knowledge (hypothesis → provisional → confirmed)
3. **Sensory** (`03_Sensory_memory/`): Sensory perception data (NO interpretation allowed)
4. **User Block** (`07_User_block/`): High-priority user facts (max 10 entries)

**Session Lifecycle**:
```python
msp = MSP(validation_mode="strict")  # "strict" | "warn" | "off"
msp.load_origin("EVA")                # Load master state (read-only)
instance_id = msp.create_instance()   # Create sandbox
msp.start_session(instance_id)        # Start session

# Write during session
msp.write_episode(episode_data, ri_level="L3")        # RI filtering: L1/L2/L3
msp.write_semantic(concept, definition, episode_id)   # Auto-confidence scoring

msp.end_session()                     # Create Session_memory_*.json
msp.consolidate_to_origin()           # Merge to master, increment version
```

**Validation Layer** (Phase 2A - Production Ready):
- **Episodic Validator**: 5-phase validation (structural, epistemic, state, crosslinks, forbidden)
- **Semantic Validator**: Conflict detection + confidence threshold (consolidate only if confidence > 0.7)
- **Sensory Validator**: NO interpretation enforcement (rejects emotional/intent language)
- **Confidence System**: 9 update signals with loop protection (2-3 attempts general, 3-4 health/safety)
- **Modes**: `strict` (reject invalid), `warn` (log + accept), `off` (no validation)

**RI-Level Filtering**:
- **L1** (smalltalk): episode_id + timestamp + state only
- **L2** (light): + summary
- **L3+** (full): complete episode with all fields

**Confidence Update System**:
```python
from validation import UpdateSignal, ConfidenceUpdater

updater = ConfidenceUpdater()
entry = updater.update_entry(entry, [
    UpdateSignal.USER_AFFIRMATION,  # +0.30, single use, force confirmed
    UpdateSignal.REPEATED_OCCURRENCE,  # +0.05, max 3x
    UpdateSignal.CONFLICT_DETECTED,    # -0.20
])
# Epistemic status auto-updates: confidence ≥ 0.80 → "confirmed"
```

**Critical Rules**:
- Episodes are append-only and immutable
- Master state untouched during conversation
- Session buffer deleted ONLY after consolidation
- LLM proposes, MSP validates and writes
- Max 30 episodes per session (enforced)
- Consolidation: 8 Sessions → 1 Core, 8 Cores → 1 Sphere (auto-tracking)

**Validation Specs**: `Episodic_MSP_Validation_Checklist.yaml`, `Semantic_Confidence_Update_Rules.yaml`, `*_LLM_Proposal_Contract.yaml`

### 9. GKS (Genesis Knowledge System)
**Location**: `Genesis Knowledge System/`

Constitutional read-only knowledge authority:

**Access Control**:
- **Allowed**: MSP, Policy_Engine, Persona_Engine
- **Forbidden**: LLM, Sensory_Layer, ESS, EVA_Matrix, Reflex_Engine

**Query Types**:
- `principle_query`: Core principles and constraints
- `protocol_query`: Procedural guidance
- `alignment_check`: Validate actions against core identity

**Modification**: Governance mode only, never at runtime.

**Spec**: `GKS_Interface_Spec.yaml`

### 10. EVA Tool (Unified Interface)
**Location**: `Orchestrator/eva_tool.py`

Unified tool interface that integrates all EVA pipeline components for LLM consumption.

**Architecture**:
- Single entry point for complete EVA processing
- Session management (start/end with ESS + MSP)
- Deterministic pipeline execution
- Structured output for LLM Phase 2

**Pipeline Integration**:
```python
stimulus_vector → EHM → ESS → EVA Matrix → Artifact Qualia → RMS → Pulse → Output
```

**Input**:
- `stimulus_vector`: From LLM Phase 1 (e.g., `{"stress": 0.8, "warmth": 0.3}`)
- `user_context`: Optional context from CIN
- `ri_data`: RI metrics for Pulse Engine
- `umbrella`: Safety level data
- `delta_t_ms`: Time delta (default 33ms)

**Output** (`EVAToolResult`):
```python
{
  "emotion_state": {...},          # 9D EVA Matrix state
  "pulse_snapshot": {              # Pulse mode, arousal, flags
    "pulse_mode": "DEEP_CARE",
    "arousal_level": 0.75,
    "llm_prompt_flags": {
      "warmth": 0.95,
      "directness": 0.3,
      "playfulness": 0.1,
      "formality": 0.4,
      "meta_level": 0.6
    },
    "safety_actions": {...},
    "pacing": {...}
  },
  "reflex_directives": {...},      # Urgency, cognitive drive, withdrawal
  "qualia_snapshot": {...},        # Phenomenological state
  "memory_encoding": {...},        # RMS output + trauma flag
  "memory_refs": [...],            # MSP episode references
  "allowed_recall": [...]          # Memory for LLM
}
```

**Test Coverage**: `test_orchestrator_basic.py`

**Invariants**:
- All pipeline execution is deterministic
- MSP operations are optional (enable_msp flag)
- Trauma protection active via RMS
- Safety actions computed by Pulse Engine

### 11. Two-Phase Orchestrator
**Location**: `Orchestrator/two_phase_orchestrator.py`

Complete LLM inference orchestrator implementing EVA's two-phase model.

**Phase 1: Cognitive Scan**
```
User Input → CIN inject context → LLM parse
  ↓
LLM outputs JSON:
{
  "intent": "user wants X",
  "stimulus_vector": {"stress": 0.8, ...},
  "emotion_detected": "anxious",
  "call_eva_tool": true,
  "reasoning": "..."
}
```

**EVA Tool Call** (if needed):
```
stimulus_vector → EVA Tool → EVAToolResult
```

**Phase 2: Response Shaping**
```
Tool results → LLM with constraints → User response

Constraints:
- Current pulse mode (CALM_SUPPORT, DEEP_CARE, EMERGENCY_HOLD, etc.)
- Arousal/valence levels
- Threat level & trauma flag
- Reflex directives (urgency, cognitive_drive, social_warmth, withdrawal)
- LLM prompt flags (warmth, directness, playfulness, formality, meta_level)
- Safety actions
- Pacing rules
```

**Key Features**:
- Separates understanding (Phase 1) from expression (Phase 2)
- Deterministic state transformation between phases
- Constraint-based response generation
- Fine-grained tone control via prompt flags
- Safety action enforcement

**Usage**:
```python
orchestrator = TwoPhaseOrchestrator(enable_msp=True)
orchestrator.start_session("session_001")

result = orchestrator.process(
    user_input="I'm feeling really stressed...",
    force_eva_tool=False  # Let Phase 1 decide
)

print(result.final_response)  # EVA's response
orchestrator.end_session()
```

**Test Status**: Structure validated, requires API key for LLM testing

### 12. LLM Bridge
**Location**: `Orchestrator/llm_bridge.py`

Google Gemini API adapter (currently using `gemini-2.0-flash-exp`):
- Combines CIN payload + system instructions
- Handles API errors gracefully
- Requires `GOOGLE_API_KEY` or `GEMINI_API_KEY` in `.env`

## Development Commands

This is a Python codebase using Google Gemini API.

### Setup
```bash
# Install dependencies (assuming requirements.txt exists)
pip install google-generativeai python-dotenv numpy

# Set up API key
echo "GOOGLE_API_KEY=your_key_here" > .env
```

### Running Individual Components

**EHM (Emotive Hormone Mapper)**:
```bash
cd "E:\The Human Algorithm\T2\EVA 7.0\ESS_Emotive_Signaling_System"
python EHM.py
```

**ESS (Emotive Signaling System)**:
```bash
cd "E:\The Human Algorithm\T2\EVA 7.0\ESS_Emotive_Signaling_System"
python ESS.py
```

**EVA Matrix Engine**:
```bash
cd "E:\The Human Algorithm\T2\EVA 7.0\EVA_Metric"
python eva_matrix_engine.py
```

**RMS (Resonance Memory System)**:
```bash
cd "E:\The Human Algorithm\T2\EVA 7.0\Resonance_Memory_System"
python rms_v6.py
```

**Artifact Qualia**:
```bash
cd "E:\The Human Algorithm\T2\EVA 7.0\Artifact_Qualia"
python Artifact_Qualia.py
```

**LLM Bridge**:
```bash
cd "E:\The Human Algorithm\T2\EVA 7.0\Orchestrator"
python llm_bridge.py
```

### Running Full Integration

**Complete Pipeline Demo** (EHM → ESS → EVA Matrix → Artifact Qualia → RMS):
```bash
cd "E:\The Human Algorithm\T2\EVA 7.0"
python integration_demo.py
```

This demonstrates three scenarios:
1. High Stress & Anxiety
2. Warmth & Connection
3. Mixed (Stress + Hope)

**EVA Tool Test** (Unified interface with Pulse Engine):
```bash
cd "E:\The Human Algorithm\T2\EVA 7.0\Orchestrator"
python eva_tool.py
```

Tests:
1. High stress scenario → EMERGENCY_HOLD mode
2. Warmth & connection → DEEP_CARE mode

**Orchestrator Basic Test** (Without LLM):
```bash
cd "E:\The Human Algorithm\T2\EVA 7.0"
python test_orchestrator_basic.py
```

Tests:
1. EVA Tool integration (3 scenarios)
2. Orchestrator structure validation

**Two-Phase Orchestrator Test** (With LLM - requires API key):
```bash
# Set up API key first
echo "GOOGLE_API_KEY=your_key_here" > .env

# Run orchestrator
cd "E:\The Human Algorithm\T2\EVA 7.0\Orchestrator"
python two_phase_orchestrator.py
```

Tests:
1. Simple greeting (Phase 1 only)
2. Emotional content (Phase 1 → EVA Tool → Phase 2)

**MSP Validation Tests** (Phase 2A):
```bash
cd "E:\The Human Algorithm\T2\EVA 7.0"

# Basic validation integration tests (4 tests)
python test_validation.py

# Comprehensive validation tests (semantic, sensory, confidence, loop protection)
python test_validation_comprehensive.py
```

Test coverage:
- Episodic validation (5-phase: structural, epistemic, state, crosslinks, forbidden)
- Semantic conflict detection + confidence scoring
- Sensory no-interpretation enforcement
- Clarification loop protection (stakes-based limits)
- Consolidation threshold filtering (confidence > 0.7)

## Key Architectural Invariants

### Separation of Concerns

1. **EHM**: Stimulus mapping only
   - Pure mathematical transformation
   - NO language processing
   - NO emotion labels
   - NO decision-making

2. **ESS**: Physiology only (hormones, reflexes)
   - NO memory read/write
   - NO language processing
   - NO phenomenology interpretation

3. **EVA Matrix**: Psychological state transformation only
   - NO emotion labels (only continuous values)
   - NO decision-making
   - NO memory access

4. **Artifact Qualia**: Phenomenological integration only
   - NO memory admission
   - NO optimization
   - NO relationship evaluation

5. **RMS**: Memory encoding only
   - NO admission decisions
   - NO importance evaluation
   - NO semantic interpretation
   - Color generation from EVA Matrix ONLY

6. **RIM**: Impact measurement only
   - NO memory admission control
   - NO good/bad evaluation
   - NO trauma override

7. **MSP**: Memory persistence + validation only
   - LLM proposes, MSP validates and writes
   - NO direct LLM write access
   - Session boundary enforcement (max 30 episodes)
   - Validation modes: strict/warn/off
   - Confidence-based consolidation (semantic > 0.7 only)
   - Loop protection on clarification attempts

8. **GKS**: Constitutional knowledge only
   - Read-only at runtime
   - NO LLM modification
   - MSP-gated access

### Data Flow Direction

```
ESC (23 chemicals) → Functional Groups (7) → EVA Matrix (9D)
                                                    ↓
                                          Artifact Qualia
                                                    ↓
                                              RMS Encoding
                                                    ↓
                              RI/RIM → MSP Session Buffer → Consolidation
```

### Forbidden Actions

- ESS/RMS/Qualia: NO memory read/write
- EVA Matrix/RMS: NO emotion labels (only continuous values)
- LLM: NO direct memory write, NO hormone simulation
- Any component: NO self-modification of core constraints
- RIM: NO memory admission decisions

### State Management

- **ESS**: PK state (`D_Remaining`, `D_Cumulative`, receptor `internalization`)
- **EVA Matrix**: 9D state with weighted momentum (80/20 split)
- **RMS**: Transient smoothing (`_last_color`, `_last_intensity`)
- **RIM**: Previous impact value for trend detection
- **Persistent State**: Lives in MSP session buffers → master state on consolidation

## Schema Validation

When working with memory structures, validate against:
- `Episodic_Memory_Schema_v2.json`
- `Semantic_Memory_Schema_v2.json`
- `Sensory_Memory_Schema_v2.json`
- `R_profile.schema.json`
- `ESS_Output_Schema.json`

## Interface Contracts

System boundaries defined via YAML:
- `ESS_Interface.yaml` - ESS integration boundaries
- `RMS_Interface.yaml` - RMS integration boundaries
- `Artifact_Qualia.yaml` - Qualia integration
- `CIN_spec.yaml` - Context injection specification
- `GKS_Interface_Spec.yaml` - Constitutional knowledge access

These contracts specify:
- Required inputs/outputs
- Forbidden actions
- Invariants
- Execution order
- Access control

## Implementation Guidelines

### When Extending ESS
- Preserve PK fidelity (exponential decay, saturation, absorption)
- Maintain Hill model for receptor PD
- Keep R_profile read-only (no runtime modification)
- Log all telemetry to `ESS/{ess_id}/ess_log.jsonl`
- Never add memory or language processing

### When Extending EVA Matrix
- Maintain 9D structure from spec
- Keep all values continuous [0,1] except `social_orientation` [-1,1]
- Never introduce emotion labels
- Preserve momentum weighting (80% ESC, 20% previous)
- Update via `process_tick(hormone_state)` only

### When Extending Artifact Qualia
- Keep transient (no persistent state beyond smoothing)
- No memory admission logic
- Tone labels must be non-emotional (quiet, neutral, charged, settling)
- Texture influences RMS only, not memory decisions
- Integrate EVA Matrix + RIM semantic (no numeric RIM)

### When Extending RMS
- Memory color MUST derive from EVA Matrix only
- Trauma detection uses `reflex_state.threat_level` exclusively
- Smoothing preserves continuity, NOT memory
- Never add importance scoring or semantic evaluation
- Output is encoding signal, not admission decision

### When Extending RI
- Maintain 4-component structure (ER, IF, SR, CR)
- Keep deterministic (no randomness)
- Independent of EVA Matrix (uses user/llm emotion separately)
- Output is one factor for MSP, not sole arbiter

### When Extending RIM
- Dual-layer architecture (numeric + semantic) must persist
- Numeric layer for system logging/tracking
- Semantic layer for Artifact Qualia (NO numbers to LLM)
- Never make memory admission decisions
- Conservative confidence scoring

### When Extending CIN
- Normalize ALL numbers to 2 decimals
- Enforce formatting rules (paragraph splitting, bullets)
- Block LLM self-modification attempts
- Prevent role breaks and instruction overrides
- Never let LLM simulate hormone values

### When Working with MSP
- Write to session buffer ONLY during conversations
- Master state is read-only until consolidation
- Apply consolidation rules strictly:
  - Episodes: append-only
  - Semantic: validate confidence > 0.7, deduplicate
  - States: latest wins
  - Core: conservative merge with logging
- Maintain crosslinks during consolidation
- Increment version atomically
- Delete session buffer after successful consolidation

### Crosslinking

Episodes contain references to:
- `ess_id` (ESS session)
- `matrix_snapshot_id` (EVA Matrix state)
- `rms_refs` (RMS outputs)
- `semantic_refs`, `sensory_refs`, `gks_refs`

Maintain referential integrity during consolidation.

## Directory Structure

```
EVA 7.0/
├── ESS_Emotive_Signaling_System/    # PK/PD emotive signaling
├── EVA_Metric/                      # RI, RIM, EVA Matrix engines
├── Artifact_Qualia/                 # Phenomenological integration
├── Resonance_Memory_System/         # Memory encoding (RMS)
├── Memory_&_Soul_Passaport/         # Memory schemas and versioning
├── Orchestrator/                    # LLM bridge + CIN
│   ├── CIN/                        # Context injection system
│   └── PMT/                        # Prompt rule layer
├── Genesis Knowledge System/        # Constitutional knowledge
├── 01_Episodic_memory/             # Master episodic storage
├── 02_Semantic_memory/             # Master semantic storage
├── 03_Sensory_memory/              # Master sensory storage
├── 07_User_block/                  # High-priority user facts
└── Buffer/instance_*/              # Session buffers (temporary)
```

## Common Patterns

### Full Processing Pipeline
```python
# 1. ESS processes stimulus
ess_output = ess.tick_once(stimulus_vector, D_Total_H, R_profile_path)
C_Mod = ess_output["C_Mod"]
reflex_vector = ess_output["reflex_vector"]

# 2. EVA Matrix transforms physiology to psychology
eva_output = eva_matrix.process_tick(C_Mod)
eva_state = eva_output["axes_9d"]

# 3. Artifact Qualia integrates phenomenology
qualia = artifact_qualia.integrate(eva_state, rim_semantic)

# 4. RMS encodes memory
rms_output = rms.process(eva_state, reflex_vector, rim_semantic)

# 5. MSP writes to session buffer (not master!)
msp.write_episode(sandbox_id, episode_data)
```

### Session Lifecycle
```python
# Start session
sandbox_id = msp.create_sandbox(user_id, "Session Name")

# During conversation - write to buffer only
msp.write_episode(sandbox_id, episode)
msp.update_state(sandbox_id, "ire_state", ire_data)

# End session - consolidate to master
new_master_state = msp.consolidate_session(sandbox_id)

# Next session loads updated master
next_sandbox_id = msp.create_sandbox(user_id, "Next Session")
```

## Testing Considerations

- Mock `C_Mod` states for ESS → EVA Matrix → RMS flow
- Validate schema compliance for all memory writes
- Test momentum decay in EVA Matrix (multiple ticks)
- Verify trauma de-intensification in RMS (`threat_level > 0.85`)
- Confirm session buffer isolation (no master state contamination)
- Check consolidation atomicity (rollback on error)

## Development Notes

### Current Integration Readiness

**Core Pipeline (Ready)**: ESS → Artifact Qualia → RMS
- These three components are complete and can be integrated
- ESS produces `C_Mod` and `reflex_vector`
- EVA Matrix transforms `C_Mod` to 9D psychological state
- Artifact Qualia integrates state + RIM semantic context
- RMS encodes memory texture with trauma protection

**Working Integration Path**:
```python
# This pipeline is functional
stimulus = {"threat": 0.3, "warmth": 0.7}  # Example
D_Total_H = {"CT": 50, "OX": 80, "DA": 60}  # Example hormone doses

# Run ESS
ess_output = ess.tick_once(stimulus, D_Total_H)
C_Mod = ess_output["C_Mod"]
reflex_vector = ess_output["reflex_vector"]

# Run EVA Matrix
eva_output = eva_matrix.process_tick(C_Mod)
eva_state = eva_output["axes_9d"]

# Run Artifact Qualia (requires RIM semantic)
rim_semantic = RIMSemantic(
    impact_level="medium",
    impact_trend="stable",
    affected_domains=["emotional"]
)
qualia = artifact_qualia.integrate(eva_state, rim_semantic)

# Run RMS
rim_semantic_dict = {
    "impact_level": "medium",
    "impact_trend": "stable"
}
rms_output = rms.process(eva_state, reflex_vector, rim_semantic_dict)
# rms_output contains: memory_color, intensity, trauma_flag
```

**Incomplete Components**:

1. **MSP (Memory & Soul Passport)**:
   - Schema definitions exist (`Episodic_Memory_Schema_v2.json`, etc.)
   - Versioning architecture documented (`msp_versioning_architecture.md`)
   - Implementation NOT complete
   - Session buffer and consolidation logic not implemented

2. **CIN (Context Injection & Normalization)**:
   - Specification exists (`CIN_spec.yaml`)
   - Partial implementation in `Orchestrator/CIN/`
   - Context injection logic incomplete
   - Payload building not fully operational

**Next Development Priorities**:

1. Complete MSP implementation:
   - Session buffer manager
   - Consolidation engine
   - Master state loader/saver
   - Atomic write operations

2. Complete CIN implementation:
   - Context collector (persona, state, memory)
   - Payload builder
   - Token normalization
   - Safety enforcement (prevent LLM override)

3. Integrate LLM tool calling:
   - Define EVA tool interface for LLM
   - Implement tool result formatter
   - Build two-phase inference pipeline

### Integration Notes

When implementing the full LLM pipeline:

1. **Phase 1 (Cognitive Scan)** should:
   - Use CIN to inject persona, previous context, user profile
   - Let LLM parse intent and infer stimulus candidates
   - LLM decides when to call EVA tool

2. **EVA Tool Call** should:
   - Accept: stimulus_vector (from LLM inference)
   - Run: ESS → EVA Matrix → Artifact Qualia → RMS deterministically
   - Query: MSP for memory retrieval (when MSP ready)
   - Return: Structured tool result (emotion state, reflexes, memory refs)

3. **Phase 2 (Response Shaping)** should:
   - Inject tool results back to LLM
   - Apply reflex directives as constraints
   - Filter memory to allowed references only
   - Generate final user-facing response

### File References

For implementation, refer to:
- **Flow diagram**: `flow.md` (system interaction flow)
- **ESS implementation**: `ESS_Emotive_Signaling_System/ESS.py`
- **EVA Matrix**: `EVA_Metric/eva_matrix_engine.py`
- **Artifact Qualia**: `Artifact_Qualia/Artifact_Qualia.py`
- **RMS**: `Resonance_Memory_System/rms_v6.py`
- **MSP specs**: `Memory_&_Soul_Passaport/` (schemas and architecture docs)
- **CIN specs**: `Orchestrator/CIN/CIN_spec.yaml`
- **LLM Bridge**: `Orchestrator/llm_bridge.py`
