"""
PulseEngineV2.py
EVA 7.0 Operational Rhythm Engine

Logic:
- Consumes Physiological State (C_Mod) from ESS.
- Consumes Contextual Meaning (RI) from RI Engine.
- Produces PulseSnapshot (mode, arousal, pacing, prompt_flags).
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional
import time
import json

@dataclass
class PulseSnapshot:
    pulse_id: str
    pulse_mode: str
    arousal_level: float
    valence_level: float
    cognitive_mode: str
    pacing: Dict[str, Any]
    llm_prompt_flags: Dict[str, float]
    safety_actions: Dict[str, bool]
    debug_tags: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))

class PulseEngineV2:
    def __init__(self):
        self.last_pulse: Optional[PulseSnapshot] = None
        
    def compute_pulse(self, 
                      c_mod: Dict[str, float], 
                      ri_data: Dict[str, Any], 
                      umbrella: Dict[str, Any], 
                      session_meta: Dict[str, Any],
                      eva_ri_input: Dict[str, Any] = None) -> PulseSnapshot:
        """
        Main entry point for calculating the turn-level pulse.
        """
        eva_ri_input = eva_ri_input or {}
        
        # 1. Extract Hormones (Normalized values from ESS C_Mod)
        adrenaline = c_mod.get("AD", 0.0)
        noradrenaline = c_mod.get("NA", 0.0)
        cortisol = c_mod.get("CT", 0.0)
        serotonin = c_mod.get("5HT", 0.0)
        oxytocin = c_mod.get("OX", 0.0)
        endorphin = c_mod.get("EN", 0.0)
        dopamine = c_mod.get("DA", 0.0)
        # GABA/GLU not directly in scoring formulas but useful for extensions
        
        # 2. Extract RI Metrics
        ri_l1 = ri_data.get("RI_L1", 0.0)
        ri_l2 = ri_data.get("RI_L2", 0.0)
        ri_l3 = ri_data.get("RI_L3", 0.0)
        ri_l4 = ri_data.get("RI_L4", 0.0)
        ri_l5 = ri_data.get("RI_L5", {})
        ri_global = ri_data.get("RI_global", 0.0)
        rz_state = ri_data.get("RZ_state", {"RZ_active": False})
        
        # 3. Calculate Internal Pulse Vector
        # Arousal: w1*AD + w2*NA + w3*CT + 0.2*RI_L1
        arousal_base = (0.4 * adrenaline) + (0.3 * noradrenaline) + (0.3 * cortisol)
        arousal = min(1.0, max(0.0, arousal_base + (0.2 * ri_l1)))
        
        # Valence: 0.4*5HT + 0.3*OX + 0.2*EN - 0.3*CT
        valence = min(1.0, max(0.0, (0.4 * serotonin) + (0.3 * oxytocin) + (0.2 * endorphin) - (0.3 * cortisol)))
        
        # Cognitive Pressure: 0.5*RI_L4 + 0.3*RI_L2 + 0.2*NA
        cog_pressure = min(1.0, max(0.0, (0.5 * ri_l4) + (0.3 * ri_l2) + (0.2 * noradrenaline)))
        
        # Existential Load
        existential_signal = eva_ri_input.get("existential_signal", 0.0)
        exist_clarity = 0.0
        if isinstance(ri_l5, dict):
            exist_clarity = ri_l5.get("S9_existential_clarity", 0.0)
        
        existential_load = min(1.0, max(0.0, (0.7 * existential_signal) + (0.3 * exist_clarity)))
        if rz_state.get("RZ_active"):
            existential_load = max(existential_load, 0.8)
            
        # Relational Focus
        intimacy = 0.0
        resonance = 0.0
        if isinstance(ri_l5, dict):
            intimacy = ri_l5.get("O5_intimacy", 0.0)
            resonance = ri_l5.get("O3_empathic_resonance", 0.0)
            
        relational_focus = min(1.0, max(0.0, (0.5 * oxytocin) + (0.3 * intimacy) + (0.2 * resonance)))
        
        # 4. Mode Determination
        safety_level = umbrella.get("safety_level", "LOW")
        rz_class = rz_state.get("RZ_class", "NORMAL")
        
        pulse_mode = "CALM_SUPPORT"
        prompt_flags = {"warmth": 0.7, "directness": 0.5, "playfulness": 0.3, "formality": 0.5, "meta_level": 0.3}
        
        # Core Mapping Logic
        if safety_level in ["HIGH", "CRITICAL"] or rz_class in ["RZ-Reject", "RZ-Warning+FutureMirror"]:
            pulse_mode = "EMERGENCY_HOLD"
            prompt_flags = {"warmth": 0.9, "directness": 0.6, "playfulness": 0.0, "formality": 0.7, "meta_level": 0.9}
        elif ri_l3 > 0.7 and relational_focus > 0.5:
            pulse_mode = "DEEP_CARE"
            prompt_flags = {"warmth": 0.95, "directness": 0.3, "playfulness": 0.1, "formality": 0.4, "meta_level": 0.6}
        elif cog_pressure > 0.7 and existential_load > 0.5:
            pulse_mode = "META_REFLECTION"
            prompt_flags = {"warmth": 0.7, "directness": 0.5, "playfulness": 0.2, "formality": 0.6, "meta_level": 1.0}
        elif cog_pressure > 0.5 and 0.4 <= arousal <= 0.7:
            pulse_mode = "FOCUSED_TASK"
            prompt_flags = {"warmth": 0.5, "directness": 0.8, "playfulness": 0.1, "formality": 0.6, "meta_level": 0.2}
        elif arousal > 0.5 and cog_pressure < 0.5:
            pulse_mode = "EXPLORATION"
            prompt_flags = {"warmth": 0.6, "directness": 0.4, "playfulness": 0.7, "formality": 0.3, "meta_level": 0.4}
        else:
            # Default CALM_SUPPORT
            pulse_mode = "CALM_SUPPORT"
            prompt_flags = {"warmth": 0.8, "directness": 0.4, "playfulness": 0.2, "formality": 0.4, "meta_level": 0.3}

        # 5. Pacing Rules
        pacing = {"response_length": "NORMAL", "suggestion_frequency": "NORMAL", "check_in_needed": False}
        if pulse_mode == "EMERGENCY_HOLD":
            pacing = {"response_length": "SHORT", "suggestion_frequency": "HIGH", "check_in_needed": True}
        elif pulse_mode == "DEEP_CARE":
            pacing = {"response_length": "LONG", "suggestion_frequency": "NORMAL", "check_in_needed": True}
        elif pulse_mode == "FOCUSED_TASK":
            pacing = {"response_length": "NORMAL", "suggestion_frequency": "LOW", "check_in_needed": False}

        # 6. Safety Actions
        safety_actions = {
            "soft_block": safety_level == "MEDIUM",
            "require_confirmation": safety_level in ["HIGH", "CRITICAL"],
            "suggest_break": arousal > 0.8 and cog_pressure > 0.8
        }

        # Create Snapshot
        snapshot = PulseSnapshot(
            pulse_id=f"PULSE-{int(time.time())}",
            pulse_mode=pulse_mode,
            arousal_level=round(arousal, 4),
            valence_level=round(valence, 4),
            cognitive_mode="HIGH_FOCUS" if cog_pressure > 0.7 else "NORMAL_LOAD",
            pacing=pacing,
            llm_prompt_flags=prompt_flags,
            safety_actions=safety_actions,
            debug_tags=[pulse_mode, f"A:{round(arousal,2)}", f"V:{round(valence,2)}", f"C:{round(cog_pressure,2)}"]
        )
        
        self.last_pulse = snapshot
        return snapshot

    def save_to_sot(self, snapshot: PulseSnapshot, log_path: str):
        """
        Append the pulse snapshot to the SOT log.
        """
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            log_data = {"schema_version": "sot-1.0", "data_log": []}
            
        log_data["data_log"].append(asdict(snapshot))
        
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
