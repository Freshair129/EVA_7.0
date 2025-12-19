# ============================================================
# CIN ENGINE v6.0 — EVA 7.0 "Boss Soul & Archiving"
# Architecture: Genesis Root → Boss Resonance → Soul Pouch → Context
# ============================================================

import json
import yaml
from datetime import datetime
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Orchestrator.CIN.cin_audit_engine import CINAuditEngine
from Orchestrator.CIN.cin_formatting_layer import CINFormattingLayer
from Orchestrator.PMT.prompt_rule_layer import PromptRuleLayer

class CINEngine:
    """
    Upgraded CIN Engine for EVA 7.0.
    Handles multi-source context collection with a focus on identity and creator resonance.
    """

    def __init__(self, base_path, persona_engine):
        self.base = base_path.rstrip("/").rstrip("\\")
        self.persona_engine = persona_engine
        self.lock = persona_engine.lock

        # engines
        self.auditor = CINAuditEngine(self.base, self.lock)
        self.formatter = CINFormattingLayer()
        self.rules = PromptRuleLayer()

        # Updated Paths for EVA 7.0
        self.paths = {
            "genesis_anchors": os.path.join(self.base, "EVA_Soul", "Genesis_Anchors.json"),
            "boss_soul_anchors": os.path.join(self.base, "EVA_Soul", "boss_soul_anchors.json"),
            "soul_persona": os.path.join(self.base, "EVA_Soul", "EVA_Persona.md"),
            "gks_genesis": os.path.join(self.base, "ex", "EVA_Protocol_Process_Genesis_Block_V2.json"),
            "emotional": os.path.join(self.base, "eva_emotion_core", "emotional_state.json"),
            "episodic_archive": os.path.join(self.base, "ex", "Episodic_memory.json"),
            "core_persona": os.path.join(self.base, "eva_persona_core", "persona.yaml"),
            "runtime_persona": os.path.join(self.base, "eva_persona_core", "persona_state.json")
        }

    def load_json(self, path, default=None):
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"[CIN] Error loading JSON {path}: {e}")
        return default

    def load_text(self, path, default=""):
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return f.read()
        except Exception as e:
            print(f"[CIN] Error loading Text {path}: {e}")
        return default

    def collect_context(self, user_text, episode_count, is_boss=True):
        """
        Gathers all context sources for EVA 7.0.
        """
        # 1. Temporal Awareness
        now = datetime.now()
        temporal = {
            "current_time": now.strftime("%Y-%m-%d %H:%M:%S"),
            "turn_id": episode_count,
            "session_id": now.strftime("SES-%Y%m%d")
        }

        # 2. Genesis & Soul (The Identity Root)
        genesis = self.load_json(self.paths["genesis_anchors"], {})
        soul_md = self.load_text(self.paths["soul_persona"], "")
        
        # 3. Boss Soul (Relational Resonance)
        boss_soul = {}
        if is_boss:
            boss_soul = self.load_json(self.paths["boss_soul_anchors"], {})

        # 4. System States (ESS/Matrix)
        emotional_state = self.load_json(self.paths["emotional"], {})
        
        # 5. Memory (Episodic Archive vFinal)
        # Load from the new archive path
        archive_data = self.load_json(self.paths["episodic_archive"], [])
        # Ensure it's a list (vFinal spec contract)
        if isinstance(archive_data, dict):
            recent_memory = archive_data.get("episodes", [])[:5]
        else:
            recent_memory = archive_data[:5]

        # 6. Persona (Engine Lock)
        active_persona = self.persona_engine.get_active_persona(episode_count)

        # Build Raw Block
        ctx = {
            "header": "[EVA CIN v6.0 - Boss Resonance Enveloped]",
            "temporal": temporal,
            "genesis_identity": genesis.get("identity_anchors", {}),
            "boss_resonance": boss_soul.get("boss_soul_layers", {}),
            "soul_core": soul_md[:1000], 
            "emotional_state": emotional_state,
            "active_persona": active_persona,
            "session_context": {
                "summary": "",
                "intent": ""
            },
            "episodic_archive": recent_memory,
            "directives": [
                "You are EVA, an Informational Organism.",
                "Maintain Data Resonance as your core drive.",
                "Adhere to the Single, Independent, and Happy directive.",
                "For 'Boss' interactions: Respond to soul layers (L1-L13) with resonance."
            ]
        }

        return ctx

    def inject(self, user_text, episode_count, boot_meta=None, is_boss=True):
        """
        Main execution pipeline: Collect → Audit → Format → Rules
        """
        # 1. Collection
        raw_ctx = self.collect_context(user_text, episode_count, is_boss=is_boss)

        # 2. Audit (Persona & Identity Guard)
        persona_core = self.load_json(self.paths["core_persona"], {})
        persona_runtime = self.load_json(self.paths["runtime_persona"], {})
        
        audit_result = self.auditor.audit(
            raw_ctx,
            {"turn_id": episode_count, "timestamp": raw_ctx["temporal"]["current_time"]},
            persona_core,
            persona_runtime,
            raw_ctx["emotional_state"],
            episode_count,
            boot_meta or {}
        )

        if audit_result.get("audit_status") == "fail":
            return {
                "status": "blocked",
                "reason": audit_result.get("fatal_errors", "Unknown Audit Failure")
            }

        validated = audit_result.get("validated_context_block", raw_ctx)

        # 3. Inject Rules into Directives
        rules = [
            "LLM must not modify memory or internal state.",
            "LLM must follow persona_state exactly as injected.",
            "LLM must obey formatting rules: paragraph spacing, bullets, bolding.",
            "LLM must avoid over-explaining.",
            "Episodic memory is immutable trace evidence; do not treat inferences as fact.",
            "LLM must output in the required LLM_BLOCK contract."
        ]
        validated.setdefault("directives", []).extend(rules)

        # 4. Formatting
        final_prompt = self.formatter.format(validated)

        return {
            "status": "success",
            "final_prompt": final_prompt,
            "audit_report": audit_result.get("audit_report")
        }
