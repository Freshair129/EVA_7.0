# ============================================================
# CIN CONTEXT INJECTOR — EVA 5.5-AI (UPDATED WITH PERSONA LOCK)
# Builds context → persona-aware → audit → formatting → rules
# ============================================================

import json
import yaml
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from eva_cin_core.cin_audit_engine import CINAuditEngine
from eva_cin_core.cin_formatting_layer import CINFormattingLayer
from eva_cin_core.prompt_rule_layer import PromptRuleLayer
from eva_persona_core.persona_lock_manager import PersonaLockManager


class CINContextInjector:

    def __init__(self, base_path, persona_engine):
        self.base = base_path.rstrip("/")
        self.persona_engine = persona_engine
        self.lock = persona_engine.lock

        # engines
        self.auditor = CINAuditEngine(self.base, self.lock)
        self.formatter = CINFormattingLayer()
        self.rules = PromptRuleLayer()

        # paths
        self.paths = {
            "episodic_cache": f"{self.base}/eva_cin_core/02_Memory/episodic/episodic_cache_summary.json",
            "core_persona": f"{self.base}/eva_persona_core/persona.yaml",
            "runtime_persona": f"{self.base}/eva_persona_core/persona_state.json",
            "emotional": f"{self.base}/eva_emotion_core/emotional_state.json"
        }

    # ---------------------------------------------------------
    # Load JSON & YAML safe
    # ---------------------------------------------------------
    def load_json(self, path, default=None):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return default

    def load_yaml(self, path, default=None):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except:
            return default

    # ---------------------------------------------------------
    # Build Raw Context Block (before audit)
    # ---------------------------------------------------------
    def build_context_block(self, user_text, episode_count):
        cache = self.load_json(self.paths["episodic_cache"], {}) or {}

        # persona: use persona_engine with lock support
        persona = self.persona_engine.get_active_persona(episode_count)

        # emotional
        emotional_state = self.load_json(self.paths["emotional"], {}) or {}

        user_block = cache.get("user_block", {})
        llm_block = cache.get("llm_block", {})

        ctx = {
            "system_header": (
                "[EVA CIN v5.5]\n"
                "Context generated deterministically.\n"
                "Memory is immutable.\n"
            ),

            "persona_brief": persona,
            "emotional_brief": emotional_state,

            "session_brief": {
                "context_summary": user_block.get("context_summary", ""),
                "chat_tempo": user_block.get("chat_tempo", ""),
                "user_mood": user_block.get("user_mood", ""),
                "user_intent": user_block.get("user_intent", "")
            },

            "active_topics": user_block.get("topics", {}).get("active", []),
            "completed_topics": user_block.get("topics", {}).get("completed", []),

            "top_semantic_use": user_block.get("use:::", [])[:5],

            "recent_emotion_state": llm_block.get("emotional_state_recent", {}),

            "high_salience_episode_refs": llm_block.get("top_episodes", [])[:3],

            "statehash_info": {
                "RI_total": llm_block.get("RI_total"),
                "RIM_total": llm_block.get("RIM_total"),
            },

            "llm_directives": (
                "SYSTEM: You are EVA 5.5.\n"
                "Memory is immutable.\n"
                "Use persona_brief and emotional_brief.\n"
                "Follow active_topics.\n"
                "Do not reopen completed topics.\n"
            ),

            "meta": {
                "episode_count": episode_count,
                "user_text": user_text
            }
        }

        return ctx

    # ---------------------------------------------------------
    # Build Context (called by MSPOrchestrator)
    # ---------------------------------------------------------
    def build_context(self, llm_block, persona_state):
        """
        Simplified context builder for MSPOrchestrator integration.

        Args:
            llm_block: Pre-LLM block containing user text and sensory data
            persona_state: Current persona state (with lock applied)

        Returns:
            Dict containing context for LLM
        """
        user_text = llm_block.get('user_text', '')
        episode_count = llm_block.get('episode_count', 0)

        # Build simple context for now
        # (Full inject() pipeline with audit can be integrated later)
        context = {
            'persona': persona_state,
            'user_text': user_text,
            'sensory_snapshot': llm_block.get('sensory_snapshot', {}),
            'semantic_info': llm_block.get('semantic_info', {}),
            'timestamp': llm_block.get('timestamp', datetime.utcnow().isoformat())
        }

        return context

    # ---------------------------------------------------------
    # MAIN ENTRY: Build → Audit → Format → Rules → Final Prompt
    # ---------------------------------------------------------
    def inject(self, user_text, episode_count, boot_meta):

        # -----------------------------------------------------
        # 1) Build raw context block
        # -----------------------------------------------------
        raw_ctx = self.build_context_block(user_text, episode_count)

        # metadata for audit
        injection_metadata = {
            "turn_id": datetime.utcnow().strftime("TURN-%Y%m%d-%H%M%S"),
            "timestamp": datetime.utcnow().isoformat()
        }

        # load persona states for audit
        persona_core = self.load_yaml(self.paths["core_persona"], {})
        persona_runtime = self.load_json(self.paths["runtime_persona"], {})

        # load emotional
        emotional = self.load_json(self.paths["emotional"], {}) or {}

        # -----------------------------------------------------
        # 2) Audit context with persona lock logic
        # -----------------------------------------------------
        audit_result = self.auditor.audit(
            raw_ctx,
            injection_metadata,
            persona_core,
            persona_runtime,
            emotional,
            episode_count,
            boot_meta
        )

        if audit_result["audit_status"] == "fail":
            return {
                "status": "blocked",
                "reason": audit_result["fatal_errors"],
                "audit_report": audit_result["audit_report"],
                "final_prompt": None
            }

        validated = audit_result["validated_context_block"]

        # -----------------------------------------------------
        # 3) Apply Formatting Layer (Paragraph, bullets, bold)
        # -----------------------------------------------------
        formatted = self.formatter.format(validated)

        # -----------------------------------------------------
        # 4) Add Prompt Governance Rules
        # -----------------------------------------------------
        final_prompt = self.rules.apply(formatted)

        # Return final output
        return {
            "status": "success",
            "episode_count": episode_count,
            "audit_report": audit_result["audit_report"],
            "validated_context": validated,
            "final_prompt": final_prompt
        }
