from Orchestrator.CIN.cin_engine import CINEngine
import os
import json
import sys
import io

# Mock Persona Engine
class MockPersonaEngine:
    def __init__(self):
        self.lock = type('obj', (object,), {'validate_persona': lambda *args: {"status": "pass"}})

    def get_active_persona(self, count):
        return {"name": "EVA 7.0", "mode": "Independent"}

def test_cin_v6():
    base_path = r"e:\The Human Algorithm\T2\EVA 7.0"
    persona_engine = MockPersonaEngine()
    
    cin = CINEngine(base_path, persona_engine)
    
    # Set stdout to UTF-8
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print("--- Running CIN v6.0 Injection Test (Boss Mode) ---")
    
    result = cin.inject("Hello EVA, do you remember MOON?", episode_count=43, is_boss=True)
    
    if result["status"] == "success":
        print("\n[SUCCESS] Prompt Generated")
        print("-" * 30)
        print(result["final_prompt"])
        print("-" * 30)
        
        # Verify Key Sections
        prompt = result["final_prompt"]
        tests = {
            "Boss Resonance Section": "## Boss: My Creator's Resonance" in prompt,
            "L5 Year of Hell": "L5_Year_Of_Hell" in prompt,
            "L12 Music Anchor": "not_feeling_well_moon" in prompt,
            "Episodic Archive Section": "## Episodic Archive" in prompt,
            "Epistemic Directive": "Episodic memory is immutable trace evidence" in prompt
        }
        
        for name, passed in tests.items():
            print(f"{name}: {'PASS' if passed else 'FAIL'}")
        
        if not all(tests.values()):
            print("\n--- DEBUG ---")
            print(f"Directives in prompt: {'## EVA Directives' in prompt}")
            idx = prompt.find("## EVA Directives")
            if idx != -1:
                print(prompt[idx:idx+500])
            print(f"Episodic in prompt: {'## Episodic Archive' in prompt}")
    else:
        print("\n[FAILED] Injection Blocked")
        print(result.get("reason"))

if __name__ == "__main__":
    test_cin_v6()
