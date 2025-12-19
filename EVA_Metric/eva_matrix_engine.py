import math
import yaml
from typing import Dict, Any, List, Tuple

# =========================================================================
# I. SPECIFICATION DATA (จาก EVA_MATRIX_9D_SPEC.yam.yaml)
# =========================================================================

# NOTE: ในการใช้งานจริง, ข้อมูลนี้จะถูกโหลดจากไฟล์ YAML ภายนอก
SPEC_DATA = {
    "ESC_FUNCTIONAL_GROUPS": {
        "stress_group": ["AD", "CT", "CRH", "CORT", "VP", "NPY"],
        "drive_group": ["DA", "NA", "TEST", "PEA"],
        "joy_group": ["DA", "5HT", "EN", "AEA", "PEA"],
        "warmth_group": ["OX", "PRL", "5HT", "ES", "AEA"],
        "clarity_group": ["ACh", "GLU", "BDNF", "NA", "HIS"],
        "soothe_group": ["GABA", "OX", "PRL", "AEA"],
        "aversive_group": ["DYN", "CT", "VP"],
    },
    "normalization": {
        "esc_scale": 50.0,
        "clamp_range_01": [0.0, 1.0],
        "clamp_range_signed": [-1.0, 1.0],
    },
    "matrix_5d_definition": {
        "stress_load": {"formula": "clamp01(stress_raw - soothe_raw)"},
        "social_warmth": {"formula": "clamp01(warmth_raw - aversive_raw)"},
        "drive_level": {"formula": "clamp01(drive_raw - soothe_raw)"},
        "cognitive_clarity": {"formula": "clamp01(clarity_raw)"},
        "joy_level": {"formula": "clamp01(joy_raw - aversive_raw)"},
    },
    "meta_axes": {
        "affective_stability": {"formula": "clamp01(soothe_raw - stress_raw)"},
        "social_orientation": {"formula": "normalize_signed(warmth_raw - aversive_raw)"},
    },
    "emotion_7d_categories": {
        "Fear": ["stress_load > 0.65", "cognitive_clarity < 0.4"],
        "Anger": ["stress_load > 0.55", "drive_level > 0.55", "social_warmth < 0.35"],
        "Joy": ["joy_level > 0.6", "social_warmth > 0.45"],
        "Calm": ["default"], # Simplified conditions for implementation
    },
    "final_output_format": {
        "axes_9d": [
            "stress_load",
            "social_warmth",
            "drive_level",
            "cognitive_clarity",
            "joy_level",
            "primary_axis",
            "secondary_axis",
            "affective_stability",
            "social_orientation",
        ]
    }
}

# -------------------------------------------------------------------------
# UTILITY FUNCTIONS
# -------------------------------------------------------------------------

def clamp01(x: float) -> float:
    """Clamp value to the range [0.0, 1.0]"""
    return max(0.0, min(1.0, float(x)))

def normalize_signed(x: float) -> float:
    """Clamp value to the range [-1.0, 1.0]"""
    return max(-1.0, min(1.0, float(x)))

# -------------------------------------------------------------------------
# MAIN ENGINE CLASS
# -------------------------------------------------------------------------

class EVAMatrix9D_CompleteEngine:
    """
    EVA Matrix 9D Engine ที่รวมตรรกะทั้งหมด:
    1. Adapter: ESC -> Functional Groups
    2. Calculator: 5D Core, 2D Meta, 2D Categorical
    3. State Tracker: Weighted update with momentum
    4. Encoder: 9D Vector/Matrix output
    """

    def __init__(self, spec_data: Dict[str, Any] = SPEC_DATA):
        self.spec = spec_data
        self.functional_groups = spec_data["ESC_FUNCTIONAL_GROUPS"]
        self.esc_scale = spec_data["normalization"]["esc_scale"]
        
        # 1. State Tracker (อ้างอิงจาก eva_emotional_state_9d.py)
        # ใช้แกนตามที่ SPEC กำหนดเป็นหลัก
        self.axes_9d_order = spec_data["final_output_format"]["axes_9d"]
        self.axes_9d = {axis: 0.50 for axis in self.axes_9d_order}
        
        # Weights for state smoothing (Momentum)
        self.weights = {
            "esc_state": 0.80, # น้ำหนักสำหรับ ESC-derived state
            "momentum": 0.20   # Smoothing factor (เทียบเท่า user/llm emotion ในโค้ดเดิม)
        }
        
        print("[EVAMatrix9D] Engine initialized and ready.")


    # -------------------------------------------------------------------------
    # 2. ADAPTER: ESC -> FUNCTIONAL GROUPS
    # -------------------------------------------------------------------------
    def _process_functional_groups(self, hormone_state: Dict[str, float]) -> Dict[str, float]:
        """
        รวมความเข้มข้นของ ESC (C_Mod) เข้าเป็นคะแนน Functional Raw Score
        """
        raw_scores = {}
        
        for group_name, chemicals in self.functional_groups.items():
            score = 0.0
            for chem in chemicals:
                # 1. Normalize ESC value (สมมติว่า C_Mod เป็นค่าบวก)
                normalized_cmod = hormone_state.get(chem, 0.0) / self.esc_scale
                
                # 2. Sum up
                score += normalized_cmod
            
            # Clamp Raw Score ให้อยู่ในช่วงที่เหมาะสมก่อนคำนวณแกนหลัก
            raw_scores[group_name + "_raw"] = clamp01(score)
            
        return raw_scores

    # -------------------------------------------------------------------------
    # 3. CALCULATOR: 5D Core Axes & 2D Meta Axes
    # -------------------------------------------------------------------------
    def _calculate_core_meta_axes(self, raw_scores: Dict[str, float]) -> Dict[str, float]:
        """
        คำนวณ 5D Core Axes และ 2D Meta Axes จาก Raw Scores
        """
        computed_axes = {}
        
        stress_raw = raw_scores.get("stress_group_raw", 0)
        soothe_raw = raw_scores.get("soothe_group_raw", 0)
        warmth_raw = raw_scores.get("warmth_group_raw", 0)
        aversive_raw = raw_scores.get("aversive_group_raw", 0)
        drive_raw = raw_scores.get("drive_group_raw", 0)
        clarity_raw = raw_scores.get("clarity_group_raw", 0)
        joy_raw = raw_scores.get("joy_group_raw", 0)
        
        # 5D Core Axes (จาก matrix_5d_definition)
        computed_axes["stress_load"] = clamp01(stress_raw - soothe_raw)
        computed_axes["social_warmth"] = clamp01(warmth_raw - aversive_raw)
        computed_axes["drive_level"] = clamp01(drive_raw - soothe_raw)
        computed_axes["cognitive_clarity"] = clamp01(clarity_raw)
        computed_axes["joy_level"] = clamp01(joy_raw - aversive_raw)
        
        # 2D Meta Axes (Affective Stability & Social Orientation)
        computed_axes["affective_stability"] = clamp01(soothe_raw - stress_raw)
        computed_axes["social_orientation"] = normalize_signed(warmth_raw - aversive_raw)
        
        return computed_axes

    # -------------------------------------------------------------------------
    # 4. CALCULATOR: 2D Categorical Axes & 7D Emotion Category
    # -------------------------------------------------------------------------
    def _calculate_categorical(self, computed_axes: Dict[str, float]) -> Tuple[Dict[str, float], str]:
        """
        คำนวณ Primary/Secondary Axis และหา 7D Emotion Category
        """
        core_5d = {k: v for k, v in computed_axes.items() if k in self.spec["matrix_5d_definition"]}
        
        # Primary/Secondary Axis (pick_highest_value)
        sorted_axes = sorted(core_5d.items(), key=lambda item: item[1], reverse=True)
        
        primary_axis = sorted_axes[0][0] if sorted_axes else "Calm"
        secondary_axis = sorted_axes[1][0] if len(sorted_axes) > 1 else "Neutral"
        
        categorical_axes = {
            "primary_axis": clamp01(core_5d.get(primary_axis, 0)),
            "secondary_axis": clamp01(core_5d.get(secondary_axis, 0)),
        }
        
        # 7D Emotion Category (Simplified evaluation)
        emotion_label = "Calm"
        
        # NOTE: การตรวจสอบเงื่อนไขที่ซับซ้อนตาม SPEC ต้องใช้ eval() ซึ่งถูกหลีกเลี่ยง
        # เราจะใช้การตรวจสอบเงื่อนไขแบบง่ายแทน
        if computed_axes.get("stress_load", 0) > 0.65 and computed_axes.get("cognitive_clarity", 0) < 0.4:
            emotion_label = "Fear"
        elif computed_axes.get("joy_level", 0) > 0.6:
            emotion_label = "Joy"
        # ... (เพิ่มเงื่อนไขอื่นๆ ตาม SPEC)

        return categorical_axes, emotion_label

    # -------------------------------------------------------------------------
    # 5. STATE TRACKER: Weighted Update (จาก eva_emotional_state_9d.py)
    # -------------------------------------------------------------------------
    def _weighted_state_update(self, esc_derived_axes: Dict[str, float]) -> Dict[str, float]:
        """
        อัปเดตสถานะ 9D โดยใช้ Weighted Merge ระหว่าง ESC-derived state กับ Momentum
        """
        new_axes = {}
        w = self.weights
        
        for axis in self.axes_9d_order:
            prev_value = self.axes_9d.get(axis, 0.5)
            esc_value = esc_derived_axes.get(axis, prev_value) # ESC Value is the new input
            
            # สูตร: Raw = (ESC_State * Weight_ESC) + (Previous_State * Weight_Momentum)
            raw = (esc_value * w["esc_state"]) + (prev_value * w["momentum"])
            
            # NOTE: clamp01 ถูกใช้สำหรับแกน 5D/AS แต่ SO ใช้ normalize_signed
            if axis == "social_orientation":
                new_axes[axis] = normalize_signed(raw)
            else:
                new_axes[axis] = clamp01(raw)

        # Store state
        self.axes_9d = new_axes
        return new_axes

    # -------------------------------------------------------------------------
    # 6. ORCHESTRATION & OUTPUT ENCODER (จาก eva_matrix_9d_engine.py)
    # -------------------------------------------------------------------------
    def process_tick(self, hormone_state: Dict[str, float]) -> Dict[str, Any]:
        """
        ฟังก์ชันหลัก: ดำเนินการวงจรเต็มรูปแบบ ESC -> 9D
        Args:
            hormone_state: C_Mod (ความเข้มข้นของ ESC) จาก PKPD Engine
        """
        
        # 1. ADAPTER: ESC -> Functional Raw Scores
        raw_scores = self._process_functional_groups(hormone_state)
        
        # 2. CALCULATOR: 5D Core & 2D Meta Axes (AS, SO)
        computed_axes = self._calculate_core_meta_axes(raw_scores)
        
        # 3. CALCULATOR: 2D Categorical Axes (Primary/Secondary) & 7D Emotion
        categorical_axes, emotion_label = self._calculate_categorical(computed_axes)
        
        # รวมทุกแกนที่คำนวณได้
        esc_derived_axes = {**computed_axes, **categorical_axes}

        # 4. STATE TRACKER: อัปเดตสถานะ 9D ด้วย Momentum
        final_9d_axes = self._weighted_state_update(esc_derived_axes)
        
        # 5. ENCODER: จัดรูปแบบ Output
        return self._package_output(final_9d_axes, emotion_label)


    def _package_output(self, axes: Dict[str, float], emotion_label: str) -> Dict[str, Any]:
        """รวมแพ็กเกจ output ให้ integration เรียกง่าย (จาก eva_matrix_9d_engine.py)"""
        return {
            "vector_9d": self._to_vector(axes),
            "matrix_3x3": self._to_matrix(axes),
            "axes_9d": axes,
            "emotion_label": emotion_label
        }

    def _normalize_output(self, v):
        """Normalize ค่าของ 9D ให้ความหมายเท่ากันทุกแกน (จาก eva_matrix_9d_engine.py)"""
        # ใช้ [-1.0, 1.0] เพื่อแสดงผล
        return normalize_signed(v)

    def _to_vector(self, axes: Dict[str, float]) -> List[float]:
        """แปลงผล 9D → vector 9 ค่า (จาก eva_matrix_9d_engine.py)"""
        vec = []
        for name in self.axes_9d_order:
            v = axes.get(name, 0)
            vec.append(self._normalize_output(v))
        return vec

    def _to_matrix(self, axes: Dict[str, float]) -> List[List[float]]:
        """แปลงผล 9D → 3x3 matrix (ดัดแปลงจาก eva_matrix_9d_engine.py)"""
        
        # ใช้ 9D Axes ตาม SPEC เพื่อจัดเรียง Matrix 3x3 ใหม่
        matrix_keys = self.axes_9d_order # 9 keys
        
        if len(matrix_keys) < 9:
            # ใช้ placeholder หากแกนไม่พอ (ไม่น่าเกิดขึ้นตาม SPEC)
            keys = matrix_keys + ['dummy'] * (9 - len(matrix_keys))
        else:
            keys = matrix_keys
            
        return [
            [
                self._normalize_output(axes.get(keys[0], 0)),
                self._normalize_output(axes.get(keys[1], 0)),
                self._normalize_output(axes.get(keys[2], 0)),
            ],
            [
                self._normalize_output(axes.get(keys[3], 0)),
                self._normalize_output(axes.get(keys[4], 0)),
                self._normalize_output(axes.get(keys[5], 0)),
            ],
            [
                self._normalize_output(axes.get(keys[6], 0)),
                self._normalize_output(axes.get(keys[7], 0)),
                self._normalize_output(axes.get(keys[8], 0)),
            ],
        ]

# =========================================================================
# ตัวอย่างการใช้งาน (Simulation)
# =========================================================================
if __name__ == "__main__":
    
    # Mock C_Mod State (สมมติความเข้มข้นหลัง PK)
    # Scenario: High Stress (CT, AD) และ Low Soothe (GABA)
    HIGH_STRESS_CMOD = {
        "CT": 100.0,  # Cortisol (Stress)
        "AD": 80.0,   # Adrenaline (Stress/Drive)
        "GABA": 5.0,  # Soothe (Low)
        "DA": 50.0,   # Dopamine (Drive/Joy)
        "OX": 20.0,   # Oxytocin (Warmth/Soothe)
        "ACh": 40.0,  # Clarity
        "CRH": 50.0   # Stress
    }

    engine = EVAMatrix9D_CompleteEngine()
    
    print("\n" + "="*60)
    print("🧠 EVA MATRIX 9D COMPLETE ENGINE SIMULATION")
    print("="*60)
    
    # Turn 1: High Stress Input
    print("\n--- Turn 1: High Stress Event ---")
    results_t1 = engine.process_tick(HIGH_STRESS_CMOD)
    
    print(f"Emotion Label: {results_t1['emotion_label']}")
    print("-" * 20)
    
    print("5D Core Axes (Normalized 0..1):")
    print(f"  Stress Load: {results_t1['axes_9d'].get('stress_load'):.4f}")
    print(f"  Social Warmth: {results_t1['axes_9d'].get('social_warmth'):.4f}")
    print(f"  Affective Stability (Meta): {results_t1['axes_9d'].get('affective_stability'):.4f}")
    print(f"  Primary Axis: {results_t1['axes_9d'].get('primary_axis'):.4f}")
    
    print("\n9D Vector (Normalized -1..1):")
    print(results_t1['vector_9d'])
    
    print("\n3x3 Matrix (Normalized -1..1):")
    for row in results_t1['matrix_3x3']:
        print([f"{v:.4f}" for v in row])

    # Turn 2: Low Stress Input (Testing Momentum/Decay)
    LOW_STRESS_CMOD = {
        "CT": 5.0, "AD": 2.0, "GABA": 80.0, "DA": 10.0, "OX": 50.0, "ACh": 50.0
    }
    
    print("\n" + "="*60)
    print("--- Turn 2: Calm Input (Checking Momentum) ---")
    results_t2 = engine.process_tick(LOW_STRESS_CMOD)
    
    # Stress_load ควรลดลง แต่ไม่ทันที (เนื่องจาก Momentum 0.20)
    print(f"Emotion Label: {results_t2['emotion_label']}")
    print(f"  Stress Load (T1): {results_t1['axes_9d'].get('stress_load'):.4f}")
    print(f"  Stress Load (T2): {results_t2['axes_9d'].get('stress_load'):.4f}")