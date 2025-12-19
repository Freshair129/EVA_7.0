MSP (Memory & Soul Passport) spec แบบย่อที่รวมสิ่งที่ระบบต้องการจากไฟล์ใน E:\The Human Algorithm\T2\eva (msp_versioning_architecture.md, msp.yaml) และแนวทางเวอร์ชัน/แซนด์บ็อกซ์:

1) หลักการสำคัญ

Master state อ่านอย่างเดียวระหว่าง session; เขียนเฉพาะตอน consolidate
ทุก session ทำงานใน sandbox + session buffer (เขียนได้เฉพาะ buffer)
Consolidation แบบ atomic, append-only สำหรับ episodes/index; episodes เป็น immutable
Version tracking ทุกครั้งที่ merge; session buffer เก็บ parent_version ตรวจ conflict ได้
Safety: ห้าม LLM แก้ memory โดยตรง, บังคับ session boundary, ป้องกัน user_block เขียนทับผิดที่
2) โครงสร้างไฟล์

Master: account/{user}/core/
01_Episodic_memory/Episodic_memory.json
02_Semantic_memory/Semantic_memory.json
03_Sensory_memory/Sensory_memory.json
05_Core_Memory/Core_memory.json
07_User_block/User_profile.json
09_Genesis_Knowledge_System/
10_state/{ire_state, ehm_state, rms_state, ri_state, qualia_state}.json
Sandbox: sandboxes/{sandbox_id}/session_buffer.json, metadata.json
Memory index: /01_Memory_index/Memory_index.json
Session snapshots: /03_Session_Memory/; Core/Sphere promotion: /04_Core_Memory/, /05_Sphere_Memory/
3) IO Contract (input → output)

Inputs: llm (user_text, llm_text, summary, intent, strategy, tags, turn_id, ts), statehash, RI, RIM, sensory_snapshot, user_profile_delta
Outputs: episodic_entry, episodic_summary, semantic_entry, sensory_entry, user_block_entry, memory_index, session_memory, core_memory, sphere_memory 
4) Memory Weight & Classifier

Weight components (ตัวอย่างจาก v4): RIM 0.20, RI 0.20, importance 0.20, confidence 0.20, system_extra 0.20; threshold: episodic ≥0.45, semantic ≥0.35, sensory ≥0.20, user_block ≥0.50
Classifier: มี user_profile_delta → UserBlock; intent DEFINE/EXPLAIN/IDENTIFY → Semantic; sensory_snapshot มี → Sensory; otherwise Episodic
5) Crosslink Engine

Link types: semantic, temporal, emotional, causal
บันทึก crosslinks ลง index/entry


Episodic: append_all, assign permanent id, crosslink, index
Semantic: validate_and_merge (confidence >0.7, dedup, update GKS)
State: latest_wins (option history)
Core: careful_merge (อนุรักษ์, log changes)
Session buffer ถูกลบทิ้งหลัง consolidate
9) API Surface (สรุป)

Master: load/save/get_version
Sandbox: create/load/delete (clone master ref + empty buffer)
Buffer: write_episode, update_state, get_buffer
Consolidation: consolidate_session, apply_consolidation_rules, merge_into_master