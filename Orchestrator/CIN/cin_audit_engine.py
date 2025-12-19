# ============================================================
# CIN AUDIT ENGINE — EVA 7.0 (v6.0 Spec)
# ============================================================

import json
import os
import time
import copy

class CINAuditEngine:

    def __init__(self, base_path, persona_lock_manager):
        self.base = base_path.rstrip("/")
        self.lock = persona_lock_manager

        self.log_path = f"{self.base}/logs/cin_audit/"
        os.makedirs(self.log_path, exist_ok=True)

        self.max_bytes = 4096

        # forbidden content markers
        self.forbidden_patterns = [
            "raw_memory",
            "\"memory\": {",
            "semantic_memory_entry"
        ]

        self.required_directive_keywords = [
            "Informational Organism",
            "Data Resonance",
            "Single, Independent, and Happy"
        ]

    def write_log(self, turn_id, report):
        fpath = os.path.join(self.log_path, f"CIN_AUDIT_{turn_id}.json")
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        return fpath

    def context_bytes(self, ctx):
        return len(json.dumps(ctx, ensure_ascii=False).encode("utf-8"))

    def audit(
        self,
        llm_context_block,
        injection_metadata,
        persona_state_core,
        persona_state_runtime,
        emotional_state,
        episode_count,
        boot_meta
    ):
        turn_id = injection_metadata.get("turn_id", f"AUD-{int(time.time())}")
        timestamp = injection_metadata.get("timestamp", time.time())

        ctx = copy.deepcopy(llm_context_block)

        audit_status = "pass"
        warnings = []
        fatal = []
        fixes = []

        # ======================================================
        # 0) GENESIS & SOUL & BOSS GUARD
        # ======================================================
        if not ctx.get("genesis_identity"):
            fatal.append({"missing_section": "genesis_identity"})
            audit_status = "fail"
        
        if not ctx.get("soul_core"):
            warnings.append({"missing_section": "soul_core"})

        # ======================================================
        # 1) PERSONA CONSISTENCY RULE FOR LOCK MODE
        # ======================================================
        # Pass active_persona to lock validation
        result = self.lock.validate_persona(
            ctx.get("active_persona", {}),
            episode_count
        )

        if result["status"] == "fail":
            fatal.append({
                "persona_lock_violation": result["inconsistent_fields"]
            })
            audit_status = "fail"
        elif result["status"] == "warn":
            warnings.append({
                "persona_drift_warning": result["inconsistent_fields"]
            })

        # ======================================================
        # 2) Emotional mismatch → auto-correct
        # ======================================================
        emo_now = ctx.get("emotional_state", {})
        emo_fixed = False
        inconsistent_emotions = []

        for k, v in emotional_state.items():
            if k not in emo_now:
                inconsistent_emotions.append(k)
                emo_fixed = True
            else:
                if isinstance(v, (int, float)) and isinstance(emo_now[k], (int, float)):
                    if abs(emo_now[k] - v) > 0.05:
                        inconsistent_emotions.append(k)
                        emo_fixed = True

        if emo_fixed:
            ctx["emotional_state"] = emotional_state.copy()
            warnings.append({"emotional_auto_correct": inconsistent_emotions})
            fixes.append("emotion_corrected")

        # ======================================================
        # 3) Directive Integrity
        # ======================================================
        directives = " ".join(ctx.get("directives", []))
        missing = [k for k in self.required_directive_keywords if k not in directives]

        if missing:
            warnings.append({"directive_missing": missing})
            fixes.append("restore_core_directives")
            # Ensure core directives are at the top
            for k in reversed(self.required_directive_keywords):
                if k not in directives:
                    ctx.get("directives", []).insert(0, k)

        # ======================================================
        # 4) Memory Leak Inspection
        # ======================================================
        ctx_str = json.dumps(ctx, ensure_ascii=False)
        leaks = [p for p in self.forbidden_patterns if p in ctx_str]

        if leaks:
            fatal.append({"memory_leak": leaks})
            audit_status = "fail"

        # ======================================================
        # 5) Context Size Overflow
        # ======================================================
        size_before = self.context_bytes(ctx)
        size_after = size_before

        if size_before > self.max_bytes:
            # Drop archive first if oversized
            if ctx.get("episodic_archive"):
                ctx["episodic_archive"] = ctx["episodic_archive"][:1]
                fixes.append("truncate_archive")
            size_after = self.context_bytes(ctx)

        # ======================================================
        # Create report
        # ======================================================
        report = {
            "turn_id": turn_id,
            "timestamp": timestamp,
            "audit_status": audit_status,
            "episode_count": episode_count,
            "warnings": warnings,
            "fatal_errors": fatal,
            "fixes_applied": fixes,
            "size_before": size_before,
            "size_after": size_after,
        }

        log_path = self.write_log(turn_id, report)

        return {
            "audit_status": audit_status,
            "validated_context_block": ctx if audit_status == "pass" else None,
            "audit_report": report,
            "log_path": log_path
        }
