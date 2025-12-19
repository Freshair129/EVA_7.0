# =============================================================================
# EVA LLM BRIDGE (Gemini Adapter)
# Role: Connects System Orchestrator to Google Gemini API
# Location: 01_Operation_System/Orchestrator/llm_bridge.py
# =============================================================================

import os
import google.generativeai as genai
from dotenv import load_dotenv

class LLMBridge:
    def __init__(self, model_name="gemini-2.0-flash"): # Updated to valid available model
        # 1. Load Config
        load_dotenv() # Looks for .env
        self.api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            print("[LLM-Bridge] CRITICAL: No API Key found in env!")
            self.client_ready = False
        else:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(model_name)
            self.client_ready = True
            
            # Debug: List available models
            try:
                print("[LLM-Bridge] Checking available models...")
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods:
                        print(f" - {m.name}")
            except Exception as e:
                print(f"[LLM-Bridge] List Models Failed: {e}")

            print(f"[LLM-Bridge] Configured for: {model_name}")

    def generate(self, prompt, system_instruction=None):
        """
        Generates content from Gemini.
        Args:
            prompt (str): The combined user+context prompt.
            system_instruction (str): Optional system prompt (if model supports it).
        """
        if not self.client_ready:
            return "[SYSTEM_ERROR] LLM Bridge not configured (Missing API Key)."

        try:
            # Simple generation for now
            # Can be enhanced with chat history or system instruction handling
            final_prompt = prompt
            if system_instruction:
                final_prompt = f"System Instruction:\n{system_instruction}\n\nUser Input:\n{prompt}"
                
            response = self.model.generate_content(final_prompt)
            return response.text

        except Exception as e:
            print(f"[LLM-Bridge] API Error: {e}")
            return f"[SYSTEM_ERROR] LLM Generation Failed: {str(e)}"

# Test Block
if __name__ == "__main__":
    bridge = LLMBridge()
    if bridge.client_ready:
        print(bridge.generate("Hello EVA, are you online?"))
