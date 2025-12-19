"""
test_msp_production.py
Verification script for production-grade MSP features (Backup, Pulse, Consolidation)
"""

import sys
from pathlib import Path
import shutil
import json

# Add MSP directory to path
msp_dir = Path(__file__).parent / "Memory_&_Soul_Passaport"
sys.path.insert(0, str(msp_dir))

from MSP import MSP

def test_msp_production_flow():
    base_path = Path("test_msp_base")
    if base_path.exists():
        shutil.rmtree(base_path)
    base_path.mkdir()
    
    # Setup mock origin
    (base_path / "01_Episodic_memory").mkdir()
    (base_path / "02_Semantic_memory").mkdir()
    (base_path / "03_Sensory_memory").mkdir()
    (base_path / "07_User_block").mkdir()
    (base_path / "Buffer").mkdir()
    
    with open(base_path / "version.json", 'w') as f:
        json.dump({"version": 1}, f)
        
    with open(base_path / "01_Episodic_memory" / "Episodic_memory.json", 'w') as f:
        json.dump({"episodes": []}, f)
    with open(base_path / "02_Semantic_memory" / "Semantic_memory.json", 'w') as f:
        json.dump({"entries": []}, f)
    with open(base_path / "03_Sensory_memory" / "Sensory_memory.json", 'w') as f:
        json.dump({"entries": []}, f)

    # Initialize MSP
    msp = MSP(base_path=base_path, validation_mode="off")
    msp.load_origin("EVA")
    
    # 1. Create Instance
    instance_id = msp.create_instance("TEST_INSTANCE")
    msp.start_session("S01")
    
    # 2. Write Episode with Pulse Snapshot
    pulse_snapshot = {
        "pulse_mode": "DEEP_CARE",
        "arousal_level": 0.45,
        "llm_prompt_flags": {"warmth": 0.9}
    }
    
    episode = {
        "summary": "Testing production MSP",
        "pulse_snapshot": pulse_snapshot,
        "turns": []
    }
    
    msp.write_episode(episode)
    
    # Verify buffer contains pulse
    buffer_path = base_path / "Buffer" / "instance_TEST_INSTANCE" / "01_Episodic_memory" / "Episodic_memory.json"
    with open(buffer_path, 'r') as f:
        buf_data = json.load(f)
        written_ep = buf_data["episodes"][0]
        assert "pulse_snapshot" in written_ep["msp_metadata"]
        print("[PASS] Pulse snapshot saved in buffer metadata")

    # 3. Consolidate to Origin (Should trigger backup)
    print("\nStarting consolidation...")
    new_version = msp.consolidate_to_origin()
    assert new_version == 2
    
    # 4. Verify Backup
    backup_dir = list((base_path / "Backups").glob("Origin_v1_*"))
    assert len(backup_dir) == 1
    print(f"[PASS] Backup created: {backup_dir[0].name}")
    
    # 5. Verify Master Data
    master_path = base_path / "01_Episodic_memory" / "Episodic_memory.json"
    with open(master_path, 'r') as f:
        master_data = json.load(f)
        assert len(master_data["episodes"]) == 1
        print("[PASS] Master episodic memory updated")

    print("\n[ALL PRODUCTION MSP TESTS PASSED]")

if __name__ == "__main__":
    test_msp_production_flow()
