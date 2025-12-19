import math
from typing import Dict, Any, Tuple, List
from pydantic import BaseModel

# -------------------------------
# UTILITY FUNCTIONS
# -------------------------------

def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    """จำกัดค่าให้อยู่ในช่วงที่กำหนด (ค่าเริ่มต้น 0.0 ถึง 1.0)"""
    return max(lo, min(hi, x))

def cosine_similarity(a: Dict[str, float], b: Dict[str, float]) -> float:
    """คำนวณ Cosine Similarity สำหรับเวกเตอร์ (ใช้สำหรับ Septad/Embedding)"""
    if not a or not b: return 0.0
    dot = sum(a.get(k, 0) * b.get(k, 0) for k in (a.keys() | b.keys()))
    mag1 = math.sqrt(sum(v*v for v in a.values()))
    mag2 = math.sqrt(sum(v*v for v in b.values()))
    if mag1 == 0 or mag2 == 0: return 0.0
    return dot / (mag1 * mag2)

# -------------------------------
# DATA STRUCTURES
# -------------------------------

class MASOutput(BaseModel):
    """ผลลัพธ์หลักจากการคำนวณ MAS และ Routing"""
    MAS: float
    route: str              # "normal_ep", "filtered_ep", "trauma"
    priority: str           # "low", "medium", "high"
    intensity: float        # ความเข้มข้นทางอารมณ์ที่คำนวณได้
    should_write: bool      # ควรจัดเก็บความจำนี้หรือไม่

# -------------------------------
# CORE MAS ENGINE (Based on V5.5.2 logic)
# -------------------------------

class MASEngine:
    """
    Memory Admission Score (MAS) Engine -
    คำนวณความสำคัญในการจัดเก็บความจำและกำหนดเส้นทาง
    """

    def __init__(self):
        # สถานะภายในสำหรับ MAS V5.5.2 (เพื่อคำนวณ Drift และ Similarity)
        self.last_ri: float = 0.0
        self.last_septad: Dict[str, float] = None
        self.last_embedding: Dict[str, float] = None
        print("[MAS Engine] Initialized (Stateful V5.5.2 Core).")

    # ----------------------------------------------------------
    # 1) MEMORY COLORING SYSTEM (จาก rms.py)
    # ----------------------------------------------------------
    def _generate_memory_color(self, septad: Dict[str, float], reflex: Dict[str, float]) -> Tuple[Dict[str, float], float]:
        """
        แปลงสถานะอารมณ์ (Septad) และ Reflex เป็นเวกเตอร์สีความจำและความเข้มข้น
        """
        color = {
            "stress": clamp(septad.get("stress_load", 0), -1, 1),
            "warmth": clamp(septad.get("social_warmth", 0), -1, 1),
            "clarity": clamp(septad.get("cognitive_clarity", 0), -1, 1),
            "drive": clamp(septad.get("drive_level", 0), -1, 1),
            "joy": clamp(septad.get("joy_level", 0), -1, 1),
        }

        # Intensity Calculation
        intensity = clamp(
            abs(color["stress"]) * 0.35 +
            abs(color["joy"]) * 0.25 +
            abs(color["drive"]) * 0.20 +
            reflex.get("threat", 0) * 0.20
        )

        return color, intensity

    # ----------------------------------------------------------
    # 2) MAIN EVALUATION LOGIC
    # ----------------------------------------------------------
    def evaluate(self, ri_now: float, septad: Dict[str, float], reflex: Dict[str, float], embedding: Dict[str, float]) -> Dict[str, Any]:
        """
        คำนวณ MAS, Routing, Priority และ Memory Coloring
        """

        threat = reflex.get("threat", 0)
        
        # --- A. ROUTING LOGIC (กำหนดเส้นทางตาม Threat) ---
        if threat >= 0.70:
            route = "trauma"
            base_weight = 1.0
        elif threat >= 0.40:
            route = "filtered_ep"
            base_weight = 0.7
        else:
            route = "normal_ep"
            base_weight = 1.0

        # --- B. MAS SUBSCORES (ใช้สถานะภายใน) ---
        # 1. RI Component (Stability)
        RI_component = clamp(1 - abs(ri_now - self.last_ri))

        # 2. Emotion Component
        Emotion_component = clamp(
            (1 - septad.get("stress_load", 0)) * 0.35 +
            septad.get("social_warmth", 0) * 0.35 +
            septad.get("cognitive_clarity", 0) * 0.30
        )
        if route == "filtered_ep":
            Emotion_component = clamp(Emotion_component * 0.8 + 0.1, 0, 1)

        # 3. Reflex Component
        Reflex_component = clamp(
            (1 - threat) * 0.4 +
            reflex.get("comfort", 0) * 0.2 +
            reflex.get("curiosity", 0) * 0.4
        )
        if route == "filtered_ep":
            Reflex_component = clamp(Reflex_component + threat * 0.2, 0, 1)

        # 4. Drift Stability (เปรียบเทียบ Septad กับเทิร์นที่แล้ว)
        if self.last_septad:
            Drift_stability = clamp(cosine_similarity(septad, self.last_septad))
        else:
            Drift_stability = 0.5

        # 5. Episodic Similarity (เปรียบเทียบ Embedding กับเทิร์นที่แล้ว)
        if self.last_embedding:
            Episodic_similarity = clamp(cosine_similarity(embedding, self.last_embedding))
        else:
            Episodic_similarity = 0.5

        # --- C. FINAL MAS CALCULATION ---
        MAS = clamp(
            RI_component * 0.20 +
            Emotion_component * 0.20 +
            Reflex_component * 0.25 +
            Drift_stability * 0.20 +
            Episodic_similarity * 0.15
        )
        MAS *= base_weight

        # --- D. WRITE DECISION & PRIORITY ---
        if route == "trauma":
            should_write = True
            priority = "high"
        else:
            should_write = MAS > 0.50
            priority = (
                "high" if MAS > 0.75 else
                "medium" if MAS > 0.50 else
                "low"
            )

        # --- E. MEMORY COLORING ---
        if should_write:
            color, intensity = self._generate_memory_color(septad, reflex)
        else:
            color, intensity = {}, 0.0

        # --- F. UPDATE INTERNAL STATE ---
        self.last_ri = ri_now
        self.last_septad = septad.copy()
        self.last_embedding = embedding.copy()

        # --- G. RETURN RESULT ---
        packet = MASOutput(
            MAS=MAS,
            route=route,
            priority=priority,
            intensity=intensity,
            should_write=should_write
        )

        return {
            "MAS_Output": packet.model_dump(),
            "Color_Vector": color
        }


# =============================================================================
# ตัวอย่างการใช้งาน (Simulation)
# =============================================================================
if __name__ == "__main__":
    engine = MASEngine()

    print("="*60)
    print("🔥 MAS ENGINE SIMULATION (Memory Admission Score)")
    print("="*60)

    # 1. Turn 1: High Threat, High Drive (Should be Trauma)
    INPUT_T1 = {
        "ri_now": 0.8,
        "septad": {"stress_load": 0.9, "social_warmth": 0.1, "cognitive_clarity": 0.7, "drive_level": 1.0, "joy_level": 0.0},
        "reflex": {"threat": 0.85, "comfort": 0.1, "curiosity": 0.5},
        "embedding": {"w1": 0.5, "w2": 0.2, "w3": 0.9}
    }
    
    print("\n### Turn 1: High Threat Event (Trauma Route) ###")
    result_t1 = engine.evaluate(**INPUT_T1)
    
    print(f"| MAS:        {result_t1['MAS_Output']['MAS']:.4f}")
    print(f"| Route:      {result_t1['MAS_Output']['route']}")
    print(f"| Priority:   {result_t1['MAS_Output']['priority']}")
    print(f"| Write:      {result_t1['MAS_Output']['should_write']}")
    print(f"| Intensity:  {result_t1['MAS_Output']['intensity']:.4f}")
    print(f"| Stress Color: {result_t1['Color_Vector']['stress']:.2f}")


    # 2. Turn 2: Low Intensity, Low Threat, Similar Embedding (Should be Normal/Medium)
    INPUT_T2 = {
        "ri_now": 0.78, # Small RI change
        "septad": {"stress_load": 0.1, "social_warmth": 0.5, "cognitive_clarity": 0.8, "drive_level": 0.5, "joy_level": 0.5}, # Septad Drift
        "reflex": {"threat": 0.2, "comfort": 0.7, "curiosity": 0.7},
        "embedding": {"w1": 0.48, "w2": 0.25, "w3": 0.85} # Similar to T1
    }
    
    print("\n### Turn 2: Calm, Similar Context (Normal Route) ###")
    # MAS V5.5.2 จะใช้ self.last_... จาก T1 ในการคำนวณ Drift
    result_t2 = engine.evaluate(**INPUT_T2)
    
    print(f"| MAS:        {result_t2['MAS_Output']['MAS']:.4f}")
    print(f"| Route:      {result_t2['MAS_Output']['route']}")
    print(f"| Priority:   {result_t2['MAS_Output']['priority']}")
    print(f"| Write:      {result_t2['MAS_Output']['should_write']}")
    print(f"| Intensity:  {result_t2['MAS_Output']['intensity']:.4f}")
    
    print("\n--- Summary of Internal State Drift ---")
    # Drift Stability: MAS should be high because RI and Embedding are stable, despite Septad change.