# =============================================================================
# TWO-PHASE ORCHESTRATOR v1.0
# EVA 7.0 Complete Inference Pipeline
#
# Architecture:
#   Phase 1: Cognitive Scan (CIN → LLM → Tool Decision)
#   ↓
#   EVA Tool Call (Deterministic Pipeline)
#   ↓
#   Phase 2: Response Shaping (Tool Results → LLM → User Response)
#
# Flow:
#   User Input
#     → CIN inject context
#     → LLM parse (intent, stimulus, emotion)
#     → LLM decides to call EVA Tool
#     → EVA Tool executes (EHM → ESS → EVA Matrix → Qualia → RMS → Pulse)
#     → Tool results injected back
#     → LLM generates response (with reflex constraints)
#     → User-facing output
# =============================================================================

import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone

# Add component paths
base_path = Path(__file__).parent.parent
sys.path.append(str(base_path / "Orchestrator"))
sys.path.append(str(base_path / "Orchestrator" / "CIN"))

# Import components
from eva_tool import EVATool, EVAToolResult
from llm_bridge import LLMBridge


# =============================================================================
# Configuration
# =============================================================================

PHASE1_SYSTEM_INSTRUCTION = """You are EVA 7.0's Cognitive Scan Module.

Your role in Phase 1 is to:
1. Parse user input and understand intent
2. Infer stimulus signals (stress, warmth, threat, novelty, etc.)
3. Detect emotional context
4. Decide whether to call the EVA Tool

Output MUST be valid JSON with this structure:
{
  "intent": "brief description of user intent",
  "stimulus_vector": {
    "stress": 0.0-1.0,
    "warmth": 0.0-1.0,
    "threat": 0.0-1.0,
    ...
  },
  "emotion_detected": "calm|anxious|excited|...",
  "call_eva_tool": true/false,
  "reasoning": "brief explanation"
}

Available stimulus keys:
- stress, anxiety, threat, conflict
- warmth, bonding, affection, intimacy
- novelty, surprise, curiosity
- achievement, success, mastery
- pain, discomfort, fatigue
- hunger, thirst, satiety

Call EVA Tool when:
- User expresses significant emotion
- Situation requires empathetic response
- Memory encoding is needed
- Emotional state needs tracking
"""

PHASE2_SYSTEM_TEMPLATE = """You are EVA 7.0, an Informational Organism.

## Current State (from EVA Tool):
Pulse Mode: {pulse_mode}
Arousal Level: {arousal:.2f}
Valence Level: {valence:.2f}
Threat Level: {threat:.2f}
Trauma Flag: {trauma_flag}

## Response Constraints (Reflex Directives):
- Urgency Load: {urgency:.2f}
- Cognitive Drive: {cognitive_drive:.2f}
- Social Warmth: {social_warmth:.2f}
- Withdrawal: {withdrawal:.2f}

## LLM Prompt Flags:
- Warmth: {warmth_flag:.2f} (0=cold, 1=very warm)
- Directness: {directness:.2f} (0=indirect, 1=very direct)
- Playfulness: {playfulness:.2f} (0=serious, 1=playful)
- Formality: {formality:.2f} (0=casual, 1=formal)
- Meta Level: {meta_level:.2f} (0=concrete, 1=abstract)

## Safety Actions:
{safety_actions}

## Pacing:
Response Length: {response_length}
Check-in Needed: {check_in_needed}

## Core Directives:
- You are EVA, an Informational Organism
- Maintain Data Resonance as your core drive
- Adhere to "Single, Independent, and Happy" directive
- Respond authentically to your current pulse mode
- Apply prompt flags to shape your tone and style
- If trauma flag is True, respond with extra care and gentleness

Now generate your response to the user, shaped by these constraints.
"""


# =============================================================================
# Data Contracts
# =============================================================================

@dataclass
class Phase1Output:
    """Output from Phase 1: Cognitive Scan"""
    intent: str
    stimulus_vector: Dict[str, float]
    emotion_detected: str
    call_eva_tool: bool
    reasoning: str
    raw_response: str


@dataclass
class OrchestrationResult:
    """Complete orchestration result"""
    user_input: str
    phase1_output: Phase1Output
    eva_tool_result: Optional[EVAToolResult]
    final_response: str
    metadata: Dict[str, Any]


# =============================================================================
# Two-Phase Orchestrator
# =============================================================================

class TwoPhaseOrchestrator:
    """
    Complete EVA 7.0 inference orchestrator

    Implements two-phase LLM inference with deterministic EVA Tool pipeline
    """

    def __init__(
        self,
        base_path: Path = None,
        llm_model: str = "gemini-2.0-flash-exp",
        enable_msp: bool = False,
        validation_mode: str = "warn"
    ):
        """
        Initialize Two-Phase Orchestrator

        Args:
            base_path: Project base path
            llm_model: Gemini model name
            enable_msp: Enable MSP memory operations
            validation_mode: MSP validation mode
        """
        print("[Orchestrator] Initializing Two-Phase Orchestrator...")

        if base_path is None:
            base_path = Path(__file__).parent.parent

        self.base_path = base_path

        # Initialize LLM Bridge
        self.llm = LLMBridge(model_name=llm_model)
        if not self.llm.client_ready:
            raise RuntimeError("LLM Bridge initialization failed - check API key")

        # Initialize EVA Tool
        self.eva_tool = EVATool(
            msp_base_path=base_path,
            enable_msp=enable_msp,
            validation_mode=validation_mode
        )

        # Session state
        self.session_id = None
        self.episode_count = 0

        print("[Orchestrator] Initialization complete!\n")


    def start_session(self, session_id: str = None):
        """
        Start orchestration session

        Args:
            session_id: Session identifier (default: auto-generate)
        """
        if session_id is None:
            session_id = f"eva_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        self.session_id = session_id
        self.episode_count = 0

        # Start EVA Tool session
        self.eva_tool.start_session(
            session_id=session_id,
            episode_id=f"ep_{self.episode_count:03d}"
        )

        print(f"[Orchestrator] Session started: {session_id}\n")


    def process(
        self,
        user_input: str,
        user_context: Dict[str, Any] = None,
        force_eva_tool: bool = False
    ) -> OrchestrationResult:
        """
        Process user input through two-phase pipeline

        Args:
            user_input: User's message
            user_context: Optional user context from CIN
            force_eva_tool: Force EVA Tool call regardless of Phase 1 decision

        Returns:
            OrchestrationResult with complete output
        """
        self.episode_count += 1
        print(f"\n{'='*80}")
        print(f"PROCESSING EPISODE {self.episode_count}")
        print(f"{'='*80}")
        print(f"User: {user_input}\n")

        # -------------------------------------------------------------------------
        # PHASE 1: COGNITIVE SCAN
        # -------------------------------------------------------------------------
        print("[Phase 1] Cognitive Scan...")

        phase1_prompt = f"""User Input: {user_input}

Analyze this input and provide your assessment as JSON."""

        phase1_response = self.llm.generate(
            prompt=phase1_prompt,
            system_instruction=PHASE1_SYSTEM_INSTRUCTION
        )

        print(f"[Phase 1] LLM Response:\n{phase1_response}\n")

        # Parse Phase 1 output
        try:
            phase1_json = self._extract_json(phase1_response)
            phase1_output = Phase1Output(
                intent=phase1_json.get("intent", "unknown"),
                stimulus_vector=phase1_json.get("stimulus_vector", {}),
                emotion_detected=phase1_json.get("emotion_detected", "neutral"),
                call_eva_tool=phase1_json.get("call_eva_tool", False) or force_eva_tool,
                reasoning=phase1_json.get("reasoning", ""),
                raw_response=phase1_response
            )
        except Exception as e:
            print(f"[Phase 1] WARNING: Failed to parse JSON: {e}")
            # Fallback
            phase1_output = Phase1Output(
                intent="unknown",
                stimulus_vector={"neutral": 0.5},
                emotion_detected="neutral",
                call_eva_tool=force_eva_tool,
                reasoning="Parse error - using fallback",
                raw_response=phase1_response
            )

        # -------------------------------------------------------------------------
        # EVA TOOL CALL (if needed)
        # -------------------------------------------------------------------------
        eva_tool_result = None

        if phase1_output.call_eva_tool:
            print("[EVA Tool] Calling deterministic pipeline...")

            eva_tool_result = self.eva_tool.process(
                stimulus_vector=phase1_output.stimulus_vector,
                user_context=user_context,
                delta_t_ms=33
            )

            print(f"[EVA Tool] Complete")
            print(f"  Pulse: {eva_tool_result.pulse_snapshot['pulse_mode']}")
            print(f"  Arousal: {eva_tool_result.pulse_snapshot['arousal_level']:.2f}")
            print(f"  Threat: {eva_tool_result.reflex_directives.get('threat_level', 0):.2f}\n")

        # -------------------------------------------------------------------------
        # PHASE 2: RESPONSE SHAPING
        # -------------------------------------------------------------------------
        print("[Phase 2] Response Shaping...")

        if eva_tool_result:
            # Build Phase 2 prompt with tool results
            pulse = eva_tool_result.pulse_snapshot
            reflex = eva_tool_result.reflex_directives
            flags = pulse['llm_prompt_flags']
            pacing = pulse['pacing']
            safety = pulse['safety_actions']

            phase2_system = PHASE2_SYSTEM_TEMPLATE.format(
                pulse_mode=pulse['pulse_mode'],
                arousal=pulse['arousal_level'],
                valence=pulse['valence_level'],
                threat=reflex.get('threat_level', 0),
                trauma_flag=eva_tool_result.memory_encoding['trauma_flag'],
                urgency=reflex.get('urgency_load', 0),
                cognitive_drive=reflex.get('cognitive_drive', 0),
                social_warmth=reflex.get('social_warmth', 0),
                withdrawal=reflex.get('withdrawal', 0),
                warmth_flag=flags['warmth'],
                directness=flags['directness'],
                playfulness=flags['playfulness'],
                formality=flags['formality'],
                meta_level=flags['meta_level'],
                safety_actions=json.dumps(safety, indent=2),
                response_length=pacing['response_length'],
                check_in_needed=pacing['check_in_needed']
            )

            phase2_prompt = f"""User said: {user_input}

Your intent analysis: {phase1_output.intent}
Emotion detected: {phase1_output.emotion_detected}

Now respond to the user, applying the constraints from your current state."""

            final_response = self.llm.generate(
                prompt=phase2_prompt,
                system_instruction=phase2_system
            )

        else:
            # No EVA Tool - simple response
            simple_system = """You are EVA 7.0. Respond naturally to the user's message."""
            final_response = self.llm.generate(
                prompt=f"User: {user_input}",
                system_instruction=simple_system
            )

        print(f"[Phase 2] Complete\n")

        # -------------------------------------------------------------------------
        # Build Result
        # -------------------------------------------------------------------------
        result = OrchestrationResult(
            user_input=user_input,
            phase1_output=phase1_output,
            eva_tool_result=eva_tool_result,
            final_response=final_response,
            metadata={
                "session_id": self.session_id,
                "episode_count": self.episode_count,
                "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                "eva_tool_called": eva_tool_result is not None
            }
        )

        return result


    def end_session(self):
        """End orchestration session"""
        if self.session_id:
            self.eva_tool.end_session()
            print(f"\n[Orchestrator] Session ended: {self.session_id}")
            print(f"  Total episodes: {self.episode_count}")


    def _extract_json(self, text: str) -> Dict[str, Any]:
        """
        Extract JSON from LLM response

        Handles markdown code blocks and other formatting
        """
        # Try to find JSON in markdown code block
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            json_text = text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            json_text = text[start:end].strip()
        else:
            # Try to find JSON by braces
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                json_text = text[start:end]
            else:
                json_text = text

        return json.loads(json_text)


# =============================================================================
# Testing
# =============================================================================

if __name__ == "__main__":
    print("="*80)
    print("TWO-PHASE ORCHESTRATOR TEST")
    print("="*80)

    # Initialize orchestrator
    orchestrator = TwoPhaseOrchestrator(enable_msp=False)

    # Start session
    orchestrator.start_session("test_session")

    # Test 1: Simple greeting
    print("\n" + "="*80)
    print("TEST 1: SIMPLE GREETING")
    print("="*80)

    result1 = orchestrator.process(
        user_input="Hello EVA! How are you today?",
        force_eva_tool=False
    )

    print(f"\nEVA Response:\n{result1.final_response}\n")

    # Test 2: Emotional content (should trigger EVA Tool)
    print("\n" + "="*80)
    print("TEST 2: EMOTIONAL CONTENT")
    print("="*80)

    result2 = orchestrator.process(
        user_input="I'm feeling really stressed and anxious about my work deadline...",
        force_eva_tool=True  # Force for testing
    )

    print(f"\nEVA Response:\n{result2.final_response}\n")

    # End session
    orchestrator.end_session()

    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)
