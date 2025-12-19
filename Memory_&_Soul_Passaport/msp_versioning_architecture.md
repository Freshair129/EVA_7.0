# MSP Memory Versioning Architecture
**Memory & Soul Passport - Versioning & Sandbox Cloning**

## 🎯 Core Concept

```
Master State (Immutable during chat)
  └─ accout/User01/core/  ← Memory Version 01

Start New Sandbox
  └─ clone(memory_version01) → sandbox/session_buffer

Conversation in Sandbox
  └─ write → session_buffer (ONLY)

User: End Session / Archive
  └─ consolidate(buffer + rules)
      → accout/User01/core/  (Memory Version 02)

Next Sandbox
  └─ load(memory_version02)
```

---

## 📁 Master State Structure

### **Location: `accout/User01/core/`**

```
accout/User01/core/
├── 01_Episodic_memory/
│   ├── episodic_memory_spec.yaml  ← Spec only
│   └── Episodic_memory.json       ← Master episodes (NOT FOUND YET)
│
├── 02_Semantic_memory/
│   └── Semantic_memory.json       ← Master knowledge
│
├── 03_Sensory_memory/
│   └── Sensory_memory.json        ← Master sensory data
│
├── 05_Core_Memory/
│   └── Core_memory.json           ← Core identity
│
├── 07_User_block/
│   └── User_profile.json          ← User profile
│
├── 09_Genesis_Knowledge_System/
│   └── GKS_data.json              ← GKS knowledge
│
└── 10_state/
    ├── ire_state.json             ← IRE state
    ├── ehm_state.json             ← EHM state
    ├── rms_state.json             ← RMS state
    ├── ri_state.json              ← RI state
    └── qualia_state.json          ← Qualia state
```

---

## 🔄 Memory Versioning Flow

### **1. System Startup**
```python
# Load Master State (Latest Version)
master_state = MSP.load_master_state("accout/User01/core/")

# Contains:
# - Episodic_memory.json (all past episodes)
# - Semantic_memory.json (knowledge base)
# - Sensory_memory.json (sensory data)
# - Core_memory.json (identity)
# - User_profile.json (user info)
# - GKS_data.json (knowledge graph)
# - All state files (IRE, EHM, RMS, RI, Qualia)
```

### **2. Create New Sandbox**
```python
# Clone Master State → Sandbox
sandbox_id = create_sandbox("Sandbox 09:30")

# Create sandbox directory
sandbox_path = f"sandboxes/{sandbox_id}/"

# Clone master state (read-only reference)
sandbox.master_ref = master_state  # Reference, not copy

# Create session buffer (writable)
sandbox.session_buffer = {
    "episodes": [],           # New episodes this session
    "semantic_updates": [],   # Knowledge candidates
    "state_changes": {},      # State deltas
    "metadata": {
        "sandbox_id": sandbox_id,
        "created_at": timestamp,
        "parent_version": master_state.version
    }
}
```

### **3. During Conversation**
```python
# User sends message
user_message = "สวัสดี EVA"

# Process through EVA pipeline
result = EVA.process(user_message, sandbox_id)

# MSP writes to SESSION BUFFER ONLY
MSP.write_to_session_buffer(sandbox_id, {
    "episode": {
        "episode_id": uuid(),
        "turn_1": {"speaker": "user", "text": user_message},
        "turn_2": {"speaker": "eva", "text": result.response},
        "RI_global": result.RI,
        "rms_annotation": result.rms_data,
        # ... full episode structure
    },
    "state_updates": {
        "ire_state": result.ire_state,
        "ehm_state": result.ehm_state,
        # ... other states
    }
})

# Master State remains UNCHANGED
```

### **4. End Session / Archive**
```python
# User clicks "Archive Session"
MSP.consolidate_session(sandbox_id)

# Process:
# 1. Load session buffer
buffer = MSP.load_session_buffer(sandbox_id)

# 2. Apply consolidation rules
consolidated = MSP.apply_consolidation_rules(buffer, master_state)

# 3. Merge into master state
master_state_v2 = MSP.merge({
    "episodic": master_state.episodic + consolidated.episodes,
    "semantic": master_state.semantic + consolidated.knowledge,
    "sensory": master_state.sensory + consolidated.sensory,
    "core": MSP.update_core(master_state.core, consolidated.core_updates),
    "states": MSP.update_states(master_state.states, consolidated.state_changes),
    "version": master_state.version + 1,
    "timestamp": now()
})

# 4. Write to master storage (atomic)
MSP.save_master_state("accout/User01/core/", master_state_v2)

# 5. Clean up session buffer
MSP.delete_session_buffer(sandbox_id)
```

### **5. Next Sandbox**
```python
# Create new sandbox
new_sandbox_id = create_sandbox("Sandbox 10:15")

# Load LATEST master state (v2)
master_state_v2 = MSP.load_master_state("accout/User01/core/")

# Clone to new sandbox
new_sandbox.master_ref = master_state_v2
new_sandbox.session_buffer = create_empty_buffer()
```

---

## 📊 Data Structures

### **Master State Schema**
```json
{
  "version": 42,
  "timestamp": "2025-12-17T09:30:00Z",
  "user_id": "User01",
  
  "episodic_memory": [
    {
      "episode_id": "ep_001",
      "session_id": "sandbox_123",
      "timestamp": "2025-12-17T09:00:00Z",
      "turn_1": {...},
      "turn_2": {...},
      "RI_global": 0.85,
      "encoding_level": "L2_standard"
    }
  ],
  
  "semantic_memory": {
    "facts": [...],
    "concepts": [...],
    "relationships": [...]
  },
  
  "core_memory": {
    "identity": {...},
    "values": [...],
    "worldview": {...}
  },
  
  "states": {
    "ire_state": {...},
    "ehm_state": {...},
    "rms_state": {...},
    "ri_state": {...},
    "qualia_state": {...}
  },
  
  "metadata": {
    "total_episodes": 1234,
    "total_sessions": 56,
    "last_consolidation": "2025-12-17T09:30:00Z"
  }
}
```

### **Session Buffer Schema**
```json
{
  "sandbox_id": "sandbox_456",
  "created_at": "2025-12-17T10:00:00Z",
  "parent_version": 42,
  
  "new_episodes": [
    {
      "episode_id": "ep_temp_001",
      "turn_1": {...},
      "turn_2": {...}
    }
  ],
  
  "semantic_candidates": [
    {
      "type": "fact",
      "content": "User likes coffee",
      "confidence": 0.9
    }
  ],
  
  "state_deltas": {
    "ire_state": {"reflex_vector": {...}},
    "ehm_state": {"eva_matrix_9d": [...]}
  },
  
  "metadata": {
    "turn_count": 5,
    "duration_seconds": 300
  }
}
```

---

## 🔐 Consolidation Rules

### **Episode Consolidation**
```yaml
rule: append_all
policy: immutable
action:
  - Append all episodes from buffer to master
  - Assign permanent episode_id
  - Update crosslinks
  - Index for search
```

### **Semantic Consolidation**
```yaml
rule: validate_and_merge
policy: selective
action:
  - Filter by confidence > 0.7
  - Check for duplicates
  - Merge with existing knowledge
  - Update GKS graph
```

### **State Consolidation**
```yaml
rule: latest_wins
policy: overwrite
action:
  - Take latest state from buffer
  - Overwrite master state
  - Preserve state history (optional)
```

### **Core Memory Consolidation**
```yaml
rule: careful_merge
policy: conservative
action:
  - Only update if high confidence
  - Preserve existing core values
  - Log all changes
```

---

## 🚀 MSP API Design

### **Master State Operations**
```python
class MSP:
    def load_master_state(user_id: str) -> MasterState:
        """Load latest master state from accout/User01/core/"""
        
    def save_master_state(user_id: str, state: MasterState):
        """Save master state atomically"""
        
    def get_master_version(user_id: str) -> int:
        """Get current master version number"""
```

### **Sandbox Operations**
```python
class MSP:
    def create_sandbox(user_id: str, name: str) -> str:
        """Create new sandbox, clone master state reference"""
        
    def load_sandbox(sandbox_id: str) -> Sandbox:
        """Load sandbox with master ref + session buffer"""
        
    def delete_sandbox(sandbox_id: str):
        """Delete sandbox and session buffer"""
```

### **Session Buffer Operations**
```python
class MSP:
    def write_episode(sandbox_id: str, episode: Episode):
        """Write episode to session buffer"""
        
    def update_state(sandbox_id: str, state_name: str, state_data: dict):
        """Update state in session buffer"""
        
    def get_session_buffer(sandbox_id: str) -> SessionBuffer:
        """Get current session buffer"""
```

### **Consolidation Operations**
```python
class MSP:
    def consolidate_session(sandbox_id: str) -> MasterState:
        """Consolidate session buffer into master state"""
        
    def apply_consolidation_rules(buffer: SessionBuffer, master: MasterState) -> ConsolidatedData:
        """Apply rules to determine what to merge"""
        
    def merge_into_master(master: MasterState, consolidated: ConsolidatedData) -> MasterState:
        """Merge consolidated data into master state"""
```

---

## 📝 File Paths

### **Master State Files**
```
accout/User01/core/01_Episodic_memory/Episodic_memory.json
accout/User01/core/02_Semantic_memory/Semantic_memory.json
accout/User01/core/03_Sensory_memory/Sensory_memory.json
accout/User01/core/05_Core_Memory/Core_memory.json
accout/User01/core/07_User_block/User_profile.json
accout/User01/core/09_Genesis_Knowledge_System/GKS_data.json
accout/User01/core/10_state/*.json
```

### **Session Buffer Files**
```
sandboxes/{sandbox_id}/session_buffer.json
sandboxes/{sandbox_id}/metadata.json
```

---

## ⚠️ Critical Rules

1. **Master State is Read-Only During Session**
   - Never write directly to master during conversation
   - Only update during consolidation

2. **Session Buffer is Temporary**
   - Created when sandbox starts
   - Deleted after consolidation
   - Not backed up

3. **Atomic Consolidation**
   - Use temp file + rename for safety
   - All-or-nothing merge
   - Rollback on error

4. **Version Tracking**
   - Increment version on every consolidation
   - Track parent version in session buffer
   - Detect conflicts if needed

5. **Immutable Episodes**
   - Episodes never change after consolidation
   - Only append, never modify

---

## 🎯 Benefits

1. **Isolation** - Each sandbox is independent
2. **Safety** - Master state protected during chat
3. **Rollback** - Can discard session without saving
4. **Concurrency** - Multiple sandboxes can exist (future)
5. **Versioning** - Track memory evolution over time

---

## 🔄 Example Flow

```
Time: 09:00
Master State v1 (100 episodes)

Time: 09:30 - Create Sandbox A
Sandbox A → clone(v1) + empty buffer

Time: 09:35 - Chat in Sandbox A
Buffer A → [ep_101, ep_102, ep_103]
Master v1 → unchanged

Time: 10:00 - Archive Sandbox A
Consolidate → Master v2 (103 episodes)
Delete Buffer A

Time: 10:30 - Create Sandbox B
Sandbox B → clone(v2) + empty buffer

Time: 10:35 - Chat in Sandbox B
Buffer B → [ep_104, ep_105]
Master v2 → unchanged

Time: 11:00 - Archive Sandbox B
Consolidate → Master v3 (105 episodes)
Delete Buffer B
```

---

## 📌 Next Steps

1. **Implement MSP Core**
   - Master state loader
   - Session buffer manager
   - Consolidation engine

2. **Define Consolidation Rules**
   - Episode rules (append all)
   - Semantic rules (validate + merge)
   - State rules (latest wins)
   - Core rules (conservative)

3. **Create File Schemas**
   - Master state JSON schema
   - Session buffer JSON schema
   - Metadata schema

4. **Build API**
   - MSP class with all operations
   - Error handling
   - Atomic writes
