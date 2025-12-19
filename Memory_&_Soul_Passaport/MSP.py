# =============================================================================
# MSP.py
# Memory & Soul Passport - Core Engine
#
# Role:
#   - Manage memory versioning with instance/sandbox isolation
#   - Session lifecycle: start → write → end → consolidate
#   - Memory hierarchy: Session → Core → Sphere
#   - RI-based filtering (L1/L2/L3+)
#
# Invariants:
#   - Master state (Origin) is read-only during session
#   - All writes go to session buffer only
#   - Max 30 episodes per session
#   - LLM proposes, MSP validates and writes
# =============================================================================

from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import time
import uuid
from datetime import datetime
import shutil

# Import validation layer
try:
    from validation.episodic_validator import EpisodicValidator
    from validation.semantic_validator import SemanticValidator
    from validation.sensory_validator import SensoryValidator
    from validation.confidence_updater import ConfidenceUpdater, UpdateSignal, StakesLevel, get_stakes_level_from_topic
    from validation.exceptions import MSPValidationError, StructuralValidationError
    VALIDATION_AVAILABLE = True
except ImportError:
    VALIDATION_AVAILABLE = False
    class MSPValidationError(Exception): pass
    class StructuralValidationError(Exception): pass
    print("[MSP] Warning: Validation layer not available")


# -----------------------------------------------------------------------------
# MSP Exceptions
# -----------------------------------------------------------------------------

class MSPError(Exception):
    """Base class for MSP-related errors"""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        self.message = message
        self.context = context or {}
        super().__init__(self.message)

class MSPConsolidationError(MSPError):
    """Raised when consolidation fails"""
    pass

class MSPBackupError(MSPError):
    """Raised when backup fails"""
    pass


# -----------------------------------------------------------------------------
# Utils
# -----------------------------------------------------------------------------

def now_iso() -> str:
    from datetime import timezone
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)


def load_json(path: Path) -> Dict[str, Any]:
    """Load JSON file, return empty dict if not exists or invalid"""
    if not path.exists():
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"[Warning] Invalid JSON in {path}: {e}")
        return {}


def save_json(path: Path, data: Dict[str, Any]):
    """Save JSON file atomically"""
    ensure_dir(path.parent)
    # Atomic write: temp file + rename
    temp_path = path.with_suffix('.tmp')
    with open(temp_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    temp_path.replace(path)


# -----------------------------------------------------------------------------
# MSP — Memory & Soul Passport
# -----------------------------------------------------------------------------

class MSP:
    """
    Memory & Soul Passport
    Manages memory versioning, session lifecycle, and consolidation
    """

    def __init__(self, base_path: Path = None, validation_mode: str = "strict"):
        if base_path is None:
            base_path = Path(__file__).parent.parent

        self.base_path = base_path

        # Directory structure
        self.episodic_dir = base_path / "01_Episodic_memory"
        self.semantic_dir = base_path / "02_Semantic_memory"
        self.sensory_dir = base_path / "03_Sensory_memory"
        self.session_dir = base_path / "04_Session_Memory"
        self.core_dir = base_path / "05_Core_Memory"
        self.sphere_dir = base_path / "06_Sphere_Memory"
        self.user_block_dir = base_path / "07_User_block"
        self.buffer_dir = base_path / "Buffer"

        # Current context
        self.origin_name: Optional[str] = None
        self.instance_id: Optional[str] = None
        self.session_id: Optional[str] = None
        self.session_episode_count: int = 0

        # Master state reference (read-only during session)
        self.master_state: Dict[str, Any] = {}

        # Validation configuration
        self.validation_mode = validation_mode  # "strict", "warn", "off"

        # Initialize validators
        if VALIDATION_AVAILABLE:
            audit_log_path = base_path / "msp_validation_audit.log"

            try:
                # Episodic validator
                episodic_schema = self.episodic_dir / "Episodic_Memory_Schema_v2.json"
                self.episodic_validator = EpisodicValidator(
                    schema_path=episodic_schema if episodic_schema.exists() else None,
                    strict_mode=(validation_mode == "strict"),
                    audit_log_path=audit_log_path
                )

                # Semantic validator
                semantic_schema = self.semantic_dir / "Semantic_Memory_Schema_v2.json"
                self.semantic_validator = SemanticValidator(
                    schema_path=semantic_schema if semantic_schema.exists() else None,
                    strict_mode=(validation_mode == "strict"),
                    audit_log_path=audit_log_path
                )

                # Sensory validator
                sensory_schema = self.sensory_dir / "Sensory_Memory_Schema_v2.json"
                self.sensory_validator = SensoryValidator(
                    schema_path=sensory_schema if sensory_schema.exists() else None,
                    strict_mode=(validation_mode == "strict"),
                    audit_log_path=audit_log_path
                )

                # Confidence updater
                self.confidence_updater = ConfidenceUpdater()

            except Exception as e:
                print(f"[MSP] Warning: Could not initialize validators: {e}")
                self.episodic_validator = None
                self.semantic_validator = None
                self.sensory_validator = None
                self.confidence_updater = None
        else:
            self.episodic_validator = None
            self.semantic_validator = None
            self.sensory_validator = None
            self.confidence_updater = None

        print(f"[MSP] Initialized at {base_path}")
        print(f"[MSP] Validation mode: {validation_mode}")

    # -------------------------------------------------------------------------
    # 1. Origin Management
    # -------------------------------------------------------------------------

    def load_origin(self, origin_name: str = "EVA") -> Dict[str, Any]:
        """
        Load Origin (master state) as read-only reference

        Args:
            origin_name: Name of the origin (default "EVA")

        Returns:
            Master state dictionary
        """
        self.origin_name = origin_name

        print(f"[MSP] Loading Origin: {origin_name}")

        # Load all memory types
        episodic_path = self.episodic_dir / "Episodic_memory.json"
        semantic_path = self.semantic_dir / "Semantic_memory.json"
        sensory_path = self.sensory_dir / "Sensory_memory.json"
        user_block_path = self.user_block_dir / "User_Block.json"

        self.master_state = {
            "origin_name": origin_name,
            "version": self._get_current_version(),
            "timestamp": now_iso(),
            "episodic_memory": load_json(episodic_path),
            "semantic_memory": load_json(semantic_path),
            "sensory_memory": load_json(sensory_path),
            "user_block": load_json(user_block_path),
            "session_count": self._count_sessions(),
            "core_count": self._count_cores(),
            "sphere_count": self._count_spheres(),
        }

        print(f"[MSP] Origin loaded (version {self.master_state['version']})")
        print(f"      Sessions: {self.master_state['session_count']}")
        print(f"      Cores: {self.master_state['core_count']}")
        print(f"      Spheres: {self.master_state['sphere_count']}")

        return self.master_state

    def _get_current_version(self) -> int:
        """Get current version number from version file"""
        version_file = self.base_path / "version.json"
        if version_file.exists():
            data = load_json(version_file)
            return data.get("version", 1)
        return 1

    def _increment_version(self):
        """Increment version number"""
        version_file = self.base_path / "version.json"
        current = self._get_current_version()
        save_json(version_file, {"version": current + 1, "updated_at": now_iso()})

    def _count_sessions(self) -> int:
        """Count total sessions"""
        if not self.session_dir.exists():
            return 0
        return len(list(self.session_dir.glob("Session_memory_S*.json")))

    def _count_cores(self) -> int:
        """Count total cores"""
        if not self.core_dir.exists():
            return 0
        return len(list(self.core_dir.glob("Core_memory_C*.json")))

    def _count_spheres(self) -> int:
        """Count total spheres"""
        if not self.sphere_dir.exists():
            return 0
        return len(list(self.sphere_dir.glob("Sphere_memory_SP*.json")))

    # -------------------------------------------------------------------------
    # 2. Instance (Sandbox) Management
    # -------------------------------------------------------------------------

    def create_instance(self, instance_id: str = None) -> str:
        """
        Create new instance/sandbox by cloning Origin

        Args:
            instance_id: Custom instance ID (default: auto-generate "THA_XX_SXX")

        Returns:
            instance_id
        """
        if self.origin_name is None:
            raise RuntimeError("Must load_origin() first")

        if instance_id is None:
            # Auto-generate: THA_01_S01
            instance_count = len(list(self.buffer_dir.glob("instance_*"))) + 1
            instance_id = f"THA_{instance_count:02d}_S01"

        self.instance_id = instance_id

        # Create instance buffer directory
        instance_path = self.buffer_dir / f"instance_{instance_id}"
        ensure_dir(instance_path)

        # Clone Origin structure
        for subdir in ["01_Episodic_memory", "02_Semantic_memory", "03_Sensory_memory"]:
            ensure_dir(instance_path / subdir)

        # Create instance metadata
        metadata = {
            "instance_id": instance_id,
            "origin_name": self.origin_name,
            "parent_version": self.master_state["version"],
            "created_at": now_iso(),
            "session_count": 0,
            "status": "active"
        }
        save_json(instance_path / "metadata.json", metadata)

        print(f"[MSP] Created instance: {instance_id}")
        print(f"      Path: {instance_path}")

        return instance_id

    def get_instance_path(self) -> Path:
        """Get current instance directory path"""
        if self.instance_id is None:
            raise RuntimeError("No active instance")
        return self.buffer_dir / f"instance_{self.instance_id}"

    # -------------------------------------------------------------------------
    # 3. Session Management
    # -------------------------------------------------------------------------

    def start_session(self, session_id: str = None) -> str:
        """
        Start new session in current instance

        Args:
            session_id: Custom session ID (default: auto-generate "S01", "S02", ...)

        Returns:
            session_id
        """
        if self.instance_id is None:
            raise RuntimeError("Must create_instance() first")

        # Auto-generate session ID
        if session_id is None:
            metadata_path = self.get_instance_path() / "metadata.json"
            metadata = load_json(metadata_path)
            session_count = metadata.get("session_count", 0) + 1
            session_id = f"S{session_count:02d}"

            # Update metadata
            metadata["session_count"] = session_count
            save_json(metadata_path, metadata)

        self.session_id = session_id
        self.session_episode_count = 0

        print(f"[MSP] Started session: {session_id}")
        print(f"      Instance: {self.instance_id}")

        return session_id

    def write_episode(
        self,
        episode_data: Dict[str, Any],
        ri_level: str = "L3"
    ) -> str:
        """
        Write episode to session buffer

        Args:
            episode_data: Episode structure from LLM + RMS
            ri_level: RI level (L1, L2, L3+) for filtering

        Returns:
            episode_id
        """
        if self.session_id is None:
            raise RuntimeError("Must start_session() first")

        # Check max episodes per session
        if self.session_episode_count >= 30:
            raise RuntimeError(f"Session {self.session_id} reached max 30 episodes. Call end_session() first.")

        # VALIDATION CHECKPOINT: Validate BEFORE processing
        if self.validation_mode != "off" and self.episodic_validator is not None:
            try:
                result = self.episodic_validator.validate(episode_data, ri_level)
                if not result.valid:
                    if self.validation_mode == "strict":
                        # Strict mode: reject invalid data
                        error_msg = f"Episodic validation failed:\n" + "\n".join(result.errors)
                        raise MSPValidationError(error_msg, errors=result.errors)
                    else:
                        # Warn mode: log warnings but continue
                        print(f"[MSP] WARNING: Validation issues found:")
                        for error in result.errors:
                            print(f"  - {error}")
            except MSPValidationError:
                raise  # Re-raise validation errors
            except Exception as e:
                print(f"[MSP] Warning: Validation check failed: {e}")

        # Generate episode_id
        episode_id = episode_data.get("episode_id")
        if episode_id is None:
            episode_id = f"ep_{self.session_id}_{self.session_episode_count + 1:03d}_{uuid.uuid4().hex[:6]}"
            episode_data["episode_id"] = episode_id

        # Apply RI-level filtering
        filtered_episode = self._apply_ri_filter(episode_data, ri_level)

        # Add metadata
        filtered_episode["msp_metadata"] = {
            "written_by": "MSP",
            "instance_id": self.instance_id,
            "session_id": self.session_id,
            "ri_level": ri_level,
            "written_at": now_iso()
        }

        # Add Pulse Snapshot if provided
        if "pulse_snapshot" in episode_data:
            filtered_episode["msp_metadata"]["pulse_snapshot"] = episode_data["pulse_snapshot"]

        # Write to buffer
        instance_path = self.get_instance_path()
        episodic_buffer = instance_path / "01_Episodic_memory" / "Episodic_memory.json"

        # Load existing buffer
        buffer_data = load_json(episodic_buffer)
        if "episodes" not in buffer_data:
            buffer_data = {
                "system": "EVA",
                "instance_id": self.instance_id,
                "session_id": self.session_id,
                "timestamp": now_iso(),
                "episodes": []
            }

        # Append episode
        buffer_data["episodes"].append(filtered_episode)

        # Save buffer
        save_json(episodic_buffer, buffer_data)

        self.session_episode_count += 1

        print(f"[MSP] Wrote episode {episode_id} (RI: {ri_level}, count: {self.session_episode_count}/30)")

        return episode_id

    def _apply_ri_filter(self, episode: Dict[str, Any], ri_level: str) -> Dict[str, Any]:
        """
        Apply RI-level filtering to episode

        L1 (smalltalk): episode_id + timestamp + state only
        L2 (light): + summary
        L3+: full episode
        """
        if ri_level == "L1":
            # Minimal: ID + timestamp + state
            return {
                "episode_id": episode.get("episode_id"),
                "timestamp": episode.get("timestamp", now_iso()),
                "emotive_snapshot": episode.get("emotive_snapshot", {})
            }

        elif ri_level == "L2":
            # Light: + summary
            return {
                "episode_id": episode.get("episode_id"),
                "timestamp": episode.get("timestamp", now_iso()),
                "summary": episode.get("summary", ""),
                "emotive_snapshot": episode.get("emotive_snapshot", {})
            }

        else:
            # L3+: Full episode
            return episode

    def write_semantic(
        self,
        concept: str,
        definition: str,
        episode_id: str,
        turn_ids: Optional[List[str]] = None,
        stakes_level: Optional[StakesLevel] = None
    ) -> str:
        """
        Write semantic entry to session buffer

        Args:
            concept: Concept name (lowercase_snake_case)
            definition: Concept definition
            episode_id: Source episode ID
            turn_ids: Optional turn IDs
            stakes_level: Stakes level (auto-detected if None)

        Returns:
            semantic_id
        """
        if self.session_id is None:
            raise RuntimeError("Must start_session() first")

        # Auto-detect stakes level if not provided
        if stakes_level is None:
            stakes_level = get_stakes_level_from_topic(concept, definition)

        # VALIDATION CHECKPOINT: Validate LLM proposal BEFORE MSP adds fields
        # (Only validate concept + definition at this stage)
        proposal_data = {
            "concept": concept,
            "definition": definition,
            "derived_from": {
                "episode_id": episode_id
            }
        }
        if turn_ids:
            proposal_data["derived_from"]["turn_ids"] = turn_ids

        if self.validation_mode != "off" and self.semantic_validator is not None:
            # Load existing entries for conflict detection
            instance_path = self.get_instance_path()
            semantic_buffer = instance_path / "02_Semantic_memory" / "Semantic_memory.json"
            buffer_data = load_json(semantic_buffer)
            existing_entries = buffer_data.get("entries", [])

            # Validate proposal (without MSP-generated fields)
            try:
                result = self.semantic_validator.validate(proposal_data, existing_entries)
                # Only check for major errors (not missing MSP fields)
                major_errors = [e for e in result.errors if not any(
                    forbidden in e for forbidden in ["semantic_id", "epistemic_status", "confidence", "created_at", "last_updated"]
                )]
                if major_errors:
                    if self.validation_mode == "strict":
                        error_msg = f"Semantic proposal validation failed:\n" + "\n".join(major_errors)
                        raise MSPValidationError(error_msg, errors=major_errors)
                    else:
                        print(f"[MSP] WARNING: Semantic validation issues:")
                        for error in major_errors:
                            print(f"  - {error}")

                # Check for conflicts
                if result.context.get("conflict_detected"):
                    print(f"[MSP] Conflict detected with: {result.context.get('conflicting_concept')}")
                    proposal_data["conflicts_with"] = [result.context.get("conflicting_concept")]

            except MSPValidationError:
                raise
            except Exception as e:
                print(f"[MSP] Warning: Semantic validation check failed: {e}")

        # NOW MSP adds authoritative fields
        # Create initial entry with confidence updater
        if self.confidence_updater:
            entry = self.confidence_updater.create_initial_entry(
                concept=concept,
                definition=definition,
                stakes_level=stakes_level
            )
        else:
            # Fallback if no confidence updater
            entry = {
                "concept": concept,
                "definition": definition,
                "epistemic_status": "hypothesis",
                "confidence": 0.3,
                "stakes_level": stakes_level.value if hasattr(stakes_level, 'value') else "medium"
            }

        # Merge proposal data
        entry.update(proposal_data)

        # Add timestamps
        entry["created_at"] = now_iso()
        entry["last_updated"] = now_iso()

        # Generate semantic_id
        semantic_id = f"sem_{self.session_id}_{uuid.uuid4().hex[:8]}"
        entry["semantic_id"] = semantic_id

        # Write to buffer
        instance_path = self.get_instance_path()
        semantic_buffer = instance_path / "02_Semantic_memory" / "Semantic_memory.json"

        buffer_data = load_json(semantic_buffer)
        if "entries" not in buffer_data:
            buffer_data = {
                "system": "EVA",
                "instance_id": self.instance_id,
                "session_id": self.session_id,
                "timestamp": now_iso(),
                "entries": []
            }

        buffer_data["entries"].append(entry)
        save_json(semantic_buffer, buffer_data)

        print(f"[MSP] Wrote semantic '{concept}' (confidence: {entry['confidence']:.2f}, stakes: {entry.get('stakes_level')})")

        return semantic_id

    # -------------------------------------------------------------------------
    # 4. Session End
    # -------------------------------------------------------------------------

    def end_session(self) -> Dict[str, Any]:
        """
        End current session and create Session_memory file

        Returns:
            Session summary
        """
        if self.session_id is None:
            raise RuntimeError("No active session")

        print(f"[MSP] Ending session {self.session_id}...")

        instance_path = self.get_instance_path()

        # Load session buffer
        episodic_buffer = instance_path / "01_Episodic_memory" / "Episodic_memory.json"
        buffer_data = load_json(episodic_buffer)

        # Check for semantic updates (related_block)
        semantic_buffer = instance_path / "02_Semantic_memory" / "Semantic_memory.json"
        semantic_data = load_json(semantic_buffer)

        # Create Session_memory file
        session_memory = {
            "session_id": self.session_id,
            "instance_id": self.instance_id,
            "created_at": now_iso(),
            "episode_count": self.session_episode_count,
            "episodes": buffer_data.get("episodes", []),
            "semantic_updates": semantic_data.get("entries", [])
        }

        # Save Session_memory
        session_file = self.session_dir / f"Session_memory_{self.session_id}.json"
        save_json(session_file, session_memory)

        print(f"[MSP] Session ended: {self.session_episode_count} episodes")
        print(f"      Saved to: {session_file}")

        # Reset session state (but keep buffer - not deleted yet)
        session_id = self.session_id
        self.session_id = None
        self.session_episode_count = 0

        return {
            "session_id": session_id,
            "episode_count": session_memory["episode_count"],
            "status": "ended"
        }

    # -------------------------------------------------------------------------
    # 5. Consolidation
    # -------------------------------------------------------------------------

    def consolidate_to_instance(self) -> str:
        """
        Consolidate and save as instance snapshot (THA_01_S01)
        Does NOT delete buffer
        """
        if self.instance_id is None:
            raise RuntimeError("No active instance")

        print(f"[MSP] Consolidating to instance snapshot: {self.instance_id}")

        # Instance already exists in Buffer/instance_XX/
        # Just mark as consolidated

        metadata_path = self.get_instance_path() / "metadata.json"
        metadata = load_json(metadata_path)
        metadata["status"] = "consolidated_instance"
        metadata["consolidated_at"] = now_iso()
        save_json(metadata_path, metadata)

        print(f"[MSP] Instance snapshot saved: {self.instance_id}")

        return self.instance_id

    def consolidate_to_origin(self) -> int:
        """
        Consolidate instance to Origin (master state)
        Updates master files and increments version
        Deletes buffer after successful consolidation
        """
        if self.instance_id is None:
            raise RuntimeError("No active instance")

        print(f"[MSP] Consolidating instance {self.instance_id} to Origin...")

        try:
            # 1. Create PRE-CONSOLIDATION BACKUP
            backup_path = self._create_origin_backup()
            print(f"[MSP] Backup created: {backup_path}")

            instance_path = self.get_instance_path()

            # 2. Load and Validate instance buffers
            episodic_buffer_path = instance_path / "01_Episodic_memory" / "Episodic_memory.json"
            semantic_buffer_path = instance_path / "02_Semantic_memory" / "Semantic_memory.json"
            sensory_buffer_path = instance_path / "03_Sensory_memory" / "Sensory_memory.json"

            if not any(p.exists() for p in [episodic_buffer_path, semantic_buffer_path, sensory_buffer_path]):
                print("[MSP] Warning: No buffers found to consolidate.")
                return self._get_current_version()

            episodic_buffer = load_json(episodic_buffer_path)
            semantic_buffer = load_json(semantic_buffer_path)
            sensory_buffer = load_json(sensory_buffer_path)

            # 3. Merge into master (with atomic writes)
            print("[MSP] Merging data...")
            self._merge_episodic(episodic_buffer)
            self._merge_semantic(semantic_buffer)
            self._merge_sensory(sensory_buffer)

            # 4. Post-Write Verification
            print("[MSP] Verifying data integrity...")
            self._verify_origin_integrity()

            # 5. Increment version
            self._increment_version()
            new_version = self._get_current_version()

            print(f"[MSP] Consolidated to Origin v{new_version}")

            # 6. Delete buffer
            self.delete_buffer()

            return new_version

        except Exception as e:
            print(f"[MSP] FATAL: Consolidation failed: {e}")
            raise MSPConsolidationError(f"Consolidation failed: {e}")

    def _create_origin_backup(self) -> Path:
        """Create a full backup of Origin directories"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_root = self.base_path / "Backups" / f"Origin_v{self._get_current_version()}_{timestamp}"
        ensure_dir(backup_root)

        dirs_to_backup = [
            "01_Episodic_memory",
            "02_Semantic_memory",
            "03_Sensory_memory",
            "07_User_block"
        ]

        try:
            for d in dirs_to_backup:
                src = self.base_path / d
                if src.exists():
                    shutil.copytree(src, backup_root / d)
            
            # Record metadata
            save_json(backup_root / "backup_metadata.json", {
                "timestamp": now_iso(),
                "prev_version": self._get_current_version(),
                "instance_id": self.instance_id
            })
            return backup_root
        except Exception as e:
            raise MSPBackupError(f"Failed to create origin backup: {e}")

    def _verify_origin_integrity(self):
        """Load master files to ensure they are valid JSON and not empty"""
        master_files = [
            self.episodic_dir / "Episodic_memory.json",
            self.semantic_dir / "Semantic_memory.json",
            self.sensory_dir / "Sensory_memory.json"
        ]

        for f in master_files:
            if not f.exists():
                continue
            data = load_json(f)
            if not data:
                raise MSPConsolidationError(f"Verification failed: File {f.name} is empty or invalid.")
            
            # Basic schema check
            if f.name == "Episodic_memory.json" and "episodes" not in data:
                 raise MSPConsolidationError(f"Verification failed: Episodic memory missing 'episodes' key.")
            if f.name == "Semantic_memory.json" and "entries" not in data:
                 raise MSPConsolidationError(f"Verification failed: Semantic memory missing 'entries' key.")

    def _merge_episodic(self, buffer_data: Dict[str, Any]):
        """Merge episodic buffer into master (append-only)"""
        master_path = self.episodic_dir / "Episodic_memory.json"
        master_data = load_json(master_path)

        if "episodes" not in master_data:
            master_data = {
                "system": "EVA",
                "user_id": "User01",
                "timestamp": now_iso(),
                "episodes": []
            }

        # Append all episodes
        new_episodes = buffer_data.get("episodes", [])
        master_data["episodes"].extend(new_episodes)
        master_data["timestamp"] = now_iso()

        save_json(master_path, master_data)
        print(f"      Merged {len(new_episodes)} episodes")

    def _merge_semantic(self, buffer_data: Dict[str, Any]):
        """Merge semantic buffer into master (validate + deduplicate)"""
        master_path = self.semantic_dir / "Semantic_memory.json"
        master_data = load_json(master_path)

        if "entries" not in master_data:
            master_data = {"entries": []}

        # Filter by confidence > 0.7 using semantic validator
        new_entries = []
        skipped_count = 0

        for entry in buffer_data.get("entries", []):
            # Use validator if available
            if self.semantic_validator is not None:
                if self.semantic_validator.validate_for_consolidation(entry):
                    new_entries.append(entry)
                else:
                    skipped_count += 1
                    print(f"      Skipped '{entry.get('concept')}' (confidence: {entry.get('confidence', 0):.2f} <= 0.7)")
            else:
                # Fallback to simple threshold check
                if entry.get("confidence", 0) > 0.7:
                    new_entries.append(entry)
                else:
                    skipped_count += 1

        # Deduplicate by concept name (keep highest confidence)
        concept_map = {}
        for entry in master_data.get("entries", []):
            concept = entry.get("concept")
            if concept:
                concept_map[concept] = entry

        for entry in new_entries:
            concept = entry.get("concept")
            if concept:
                existing = concept_map.get(concept)
                if existing:
                    # Keep entry with higher confidence
                    if entry.get("confidence", 0) > existing.get("confidence", 0):
                        concept_map[concept] = entry
                        print(f"      Updated '{concept}' with higher confidence")
                else:
                    concept_map[concept] = entry

        # Rebuild entries list
        master_data["entries"] = list(concept_map.values())

        save_json(master_path, master_data)
        print(f"      Merged {len(new_entries)} semantic entries (skipped {skipped_count})")

    def _merge_sensory(self, buffer_data: Dict[str, Any]):
        """Merge sensory buffer into master with validation"""
        master_path = self.sensory_dir / "Sensory_memory.json"
        master_data = load_json(master_path)

        if "entries" not in master_data:
            master_data = {"entries": []}

        # Validate sensory entries before merging
        new_entries = []
        skipped_count = 0

        for entry in buffer_data.get("entries", []):
            # Use validator if available
            if self.sensory_validator is not None:
                try:
                    result = self.sensory_validator.validate(entry)
                    if result.valid:
                        new_entries.append(entry)
                    else:
                        skipped_count += 1
                        print(f"      Skipped sensory entry '{entry.get('sensory_id')}': {result.errors}")
                except Exception as e:
                    print(f"      Warning: Sensory validation failed: {e}")
                    skipped_count += 1
            else:
                # No validator: accept all
                new_entries.append(entry)

        master_data["entries"].extend(new_entries)

        save_json(master_path, master_data)
        print(f"      Merged {len(new_entries)} sensory entries (skipped {skipped_count})")

    def delete_buffer(self):
        """Delete instance buffer directory"""
        if self.instance_id is None:
            raise RuntimeError("No active instance")

        instance_path = self.get_instance_path()

        if instance_path.exists():
            shutil.rmtree(instance_path)
            print(f"[MSP] Deleted buffer: {instance_path}")

        self.instance_id = None
        self.session_id = None
        self.session_episode_count = 0


# =============================================================================
# Testing
# =============================================================================

if __name__ == "__main__":
    print("="*80)
    print("MSP CORE ENGINE TEST")
    print("="*80)

    # Initialize
    msp = MSP()

    # Test 1: Load Origin
    print("\n--- Test 1: Load Origin ---")
    master = msp.load_origin("EVA")

    # Test 2: Create Instance
    print("\n--- Test 2: Create Instance ---")
    instance_id = msp.create_instance("THA_01_S01")

    # Test 3: Start Session
    print("\n--- Test 3: Start Session ---")
    session_id = msp.start_session()

    # Test 4: Write Episodes
    print("\n--- Test 4: Write Episodes ---")

    # Mock episode data
    for i in range(3):
        episode = {
            "episode_header": {
                "episode_type": "interaction"
            },
            "turns": [
                {"turn_id": "t1", "speaker": "user", "raw_text": f"Test message {i+1}"},
                {"turn_id": "t2", "speaker": "eva", "raw_text": f"Response {i+1}"}
            ],
            "emotive_snapshot": {
                "indexed_state": {
                    "eva_matrix": {"stress_load": 0.3, "social_warmth": 0.7},
                    "qualia": {"intensity": 0.5},
                    "reflex": {"threat_level": 0.2}
                },
                "crosslinks": {}
            },
            "summary": f"Test conversation {i+1}"
        }

        # Test different RI levels
        ri_level = ["L1", "L2", "L3"][i]
        msp.write_episode(episode, ri_level=ri_level)

    # Test 5: End Session
    print("\n--- Test 5: End Session ---")
    summary = msp.end_session()
    print(f"Session summary: {summary}")

    # Test 6: Consolidate to Instance
    print("\n--- Test 6: Consolidate to Instance ---")
    msp.consolidate_to_instance()

    # Test 7: Consolidate to Origin
    print("\n--- Test 7: Consolidate to Origin ---")
    new_version = msp.consolidate_to_origin()
    print(f"New Origin version: {new_version}")

    print("\n" + "="*80)
    print("MSP TEST COMPLETE")
    print("="*80)
