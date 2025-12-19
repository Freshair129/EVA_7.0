# =============================================================================
# EHM.py
# Emotive Hormone Mapper
#
# Role:
#   - Convert pre-linguistic stimulus signals to hormone secretion doses
#   - Bridge between LLM inference and ESS physiological engine
#
# Inputs:
#   - stimulus_vector (from LLM Phase 1)
#
# Outputs:
#   - D_Total_H (hormone doses for ESS)
#
# Invariants:
#   - No language processing
#   - No emotion labels
#   - Pure mathematical mapping
# =============================================================================

from typing import Dict, Any
from pathlib import Path
import yaml


# -----------------------------------------------------------------------------
# Utils
# -----------------------------------------------------------------------------

def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


# -----------------------------------------------------------------------------
# EHM — Emotive Hormone Mapper
# -----------------------------------------------------------------------------

class EHM:
    """
    Emotive Hormone Mapper
    Maps stimulus intensities to hormone secretion doses
    """

    def __init__(self, config_path: Path = None):
        if config_path is None:
            config_path = Path(__file__).parent / "stimulus.txt"

        self.config = self._load_config(config_path)
        self.chemicals = self._build_chemical_registry()

        print(f"[EHM] Loaded {len(self.chemicals)} chemicals")
        print(f"[EHM] Available stimuli: {len(self.config.get('STIMULUS_KEYS', []))}")

    # -------------------------------------------------------------------------
    # Configuration Loading
    # -------------------------------------------------------------------------

    def _load_config(self, config_path: Path) -> Dict[str, Any]:
        """Load and parse stimulus.txt configuration"""

        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse YAML
        config = yaml.safe_load(content)

        return config

    def _build_chemical_registry(self) -> Dict[str, Dict[str, Any]]:
        """Merge Hormones and Neurotransmitters into single registry"""

        registry = {}

        # Add hormones
        if "Hormones" in self.config:
            for chem_name, chem_config in self.config["Hormones"].items():
                registry[chem_name] = chem_config

        # Add neurotransmitters
        if "Neurotransmitters" in self.config:
            for chem_name, chem_config in self.config["Neurotransmitters"].items():
                registry[chem_name] = chem_config

        return registry

    # -------------------------------------------------------------------------
    # Stimulus → Dose Mapping
    # -------------------------------------------------------------------------

    def map(self, stimulus_vector: Dict[str, float]) -> Dict[str, float]:
        """
        Convert stimulus intensities to hormone doses

        Args:
            stimulus_vector: Dict of stimulus keys → intensities [0, 1]
                Example: {"stress": 0.8, "warmth": 0.3, "novelty": 0.5}

        Returns:
            D_Total_H: Dict of chemical names → doses (in medical units)
                Example: {"AD": 64.0, "CT": 16.8, "DA": 45.0, ...}
        """

        D_Total_H = {}

        for chem_name, chem_config in self.chemicals.items():
            dose = self._compute_dose(chem_name, chem_config, stimulus_vector)
            D_Total_H[chem_name] = dose

        return D_Total_H

    def _compute_dose(
        self,
        chem_name: str,
        chem_config: Dict[str, Any],
        stimulus_vector: Dict[str, float]
    ) -> float:
        """
        Compute hormone dose for a single chemical

        Formula:
            dose = baseline + sum(stimulus_intensity * weight * max_rate)
            dose = clamp(dose, 0, max_value)
        """

        # Start from baseline
        dose = chem_config.get("baseline", 0.0)

        # Get stimulus weights for this chemical
        stimulus_weights = chem_config.get("stimulus_weights", {})

        # Accumulate contributions from each stimulus
        for stim_key, stim_intensity in stimulus_vector.items():
            # Get weight for this stimulus (default 0 if not specified)
            weight = stimulus_weights.get(stim_key, 0.0)

            if weight == 0.0:
                continue

            # Get max secretion rate
            max_rate = chem_config.get("max_rate_pg_per_min", 1.0)

            # Compute contribution
            # Positive weight: increase dose
            # Negative weight: decrease dose
            contribution = stim_intensity * weight * max_rate
            dose += contribution

        # Clamp to valid range
        max_value = chem_config.get("max_value_pg", float('inf'))
        dose = clamp(dose, 0.0, max_value)

        return dose

    # -------------------------------------------------------------------------
    # Validation & Debugging
    # -------------------------------------------------------------------------

    def validate_stimulus(self, stimulus_vector: Dict[str, float]) -> bool:
        """
        Validate that stimulus vector contains valid keys and values
        """

        valid_keys = {item['key'] for item in self.config.get("STIMULUS_KEYS", [])}

        for key, value in stimulus_vector.items():
            # Check key validity
            if key not in valid_keys:
                print(f"[EHM] Warning: Unknown stimulus key '{key}'")

            # Check value range
            if not (0.0 <= value <= 1.0):
                print(f"[EHM] Warning: Stimulus '{key}' has invalid value {value} (should be [0,1])")
                return False

        return True

    def get_affected_chemicals(self, stimulus_key: str) -> list:
        """
        Get list of chemicals affected by a specific stimulus
        """

        for item in self.config.get("STIMULUS_KEYS", []):
            if item['key'] == stimulus_key:
                return item.get('affects_esc', [])

        return []

    def get_stimulus_info(self, stimulus_key: str) -> Dict[str, Any]:
        """
        Get metadata about a stimulus
        """

        for item in self.config.get("STIMULUS_KEYS", []):
            if item['key'] == stimulus_key:
                return item

        return {}

    def print_dose_breakdown(self, stimulus_vector: Dict[str, float], D_Total_H: Dict[str, float]):
        """
        Print detailed breakdown of dose calculation (for debugging)
        """

        print("\n" + "="*60)
        print("EHM DOSE BREAKDOWN")
        print("="*60)

        print("\nStimulus Vector:")
        for key, value in stimulus_vector.items():
            print(f"  {key:20s} = {value:.2f}")

        print("\nHormone Doses (Top 10):")
        sorted_doses = sorted(D_Total_H.items(), key=lambda x: x[1], reverse=True)[:10]

        for chem_name, dose in sorted_doses:
            config = self.chemicals[chem_name]
            baseline = config.get("baseline", 0)
            unit = config.get("unit", "N/A")

            # Replace Greek symbols for console compatibility
            unit = unit.replace("μ", "u").replace("Δ", "D")

            # Calculate delta from baseline
            delta = dose - baseline
            delta_pct = (delta / baseline * 100) if baseline > 0 else 0

            print(f"  {chem_name:6s} = {dose:8.2f} {unit:10s} "
                  f"(baseline: {baseline:.1f}, delta{delta:+6.1f} = {delta_pct:+5.1f}%)")

        print("="*60 + "\n")


# =============================================================================
# Testing & Examples
# =============================================================================

if __name__ == "__main__":

    # Initialize EHM
    ehm = EHM()

    print("\n" + "="*60)
    print("EHM ENGINE TEST")
    print("="*60)

    # Test 1: High Stress Scenario
    print("\n--- Test 1: High Stress Scenario ---")
    stimulus_high_stress = {
        "stress": 0.9,
        "danger": 0.7,
        "uncertainty": 0.6,
        "social_threat": 0.5
    }

    ehm.validate_stimulus(stimulus_high_stress)
    D_Total_H_stress = ehm.map(stimulus_high_stress)
    ehm.print_dose_breakdown(stimulus_high_stress, D_Total_H_stress)

    # Test 2: High Warmth/Bonding Scenario
    print("\n--- Test 2: High Warmth/Bonding Scenario ---")
    stimulus_warmth = {
        "affection": 0.9,
        "social_safety": 0.8,
        "touch": 0.7,
        "comfort": 0.6,
        "calm": 0.5
    }

    ehm.validate_stimulus(stimulus_warmth)
    D_Total_H_warmth = ehm.map(stimulus_warmth)
    ehm.print_dose_breakdown(stimulus_warmth, D_Total_H_warmth)

    # Test 3: Mixed Scenario
    print("\n--- Test 3: Mixed (Stress + Hope) Scenario ---")
    stimulus_mixed = {
        "stress": 0.6,
        "hope": 0.7,
        "novelty": 0.5,
        "cognitive_load": 0.8
    }

    ehm.validate_stimulus(stimulus_mixed)
    D_Total_H_mixed = ehm.map(stimulus_mixed)
    ehm.print_dose_breakdown(stimulus_mixed, D_Total_H_mixed)

    # Test 4: Check stimulus info
    print("\n--- Stimulus Metadata Check ---")
    print(f"'stress' affects: {ehm.get_affected_chemicals('stress')}")
    print(f"'affection' affects: {ehm.get_affected_chemicals('affection')}")

    info = ehm.get_stimulus_info('stress')
    print(f"'stress' metadata: {info}")
