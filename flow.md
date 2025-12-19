User Input
↓
CIN
- Injected Context
↓
LLM Inference (Phase 1: Cognitive Scan)
  - parse text
  - infer intent
  - infer stimulus candidates 
  - infer memory (memory_match → recall)
  - emotion match
↓
LLM Decision: CALL TOOL
↓
EVA Tool Pipeline (Deterministic)
   - ESS (EHM  →  ISR  →  IRE) 
   - Artifact_Qualia
   - CIN (MSP  →  RMS  →  TraumaStore → GKS)
↓
Tool Result Injected
  - emotion state
  - reflex directives
  - recall permission (if any)
  - memory reference, related memory
  - related knowledge form GKS
  - related semantic_memory
  - related user_block
↓
LLM Inference (Phase 2: Response Shaping)
  - read reflex
  - apply persona constraints
  - apply allowed memory only
↓
LLM Generate User-Facing Answer
