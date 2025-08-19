# ai_assistant/session_manager.py
import json
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional

from .config import ai_settings

class SessionManager:
    """Manages stateful conversation sessions with robust integrity checks."""
    
    def __init__(self):
        # Use Path.cwd() to ensure the path is relative to the project root, not user's home
        self.session_dir = ai_settings.paths.sessions_dir
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
        
    def _get_session_path(self, session_id: str) -> Path:
        """Constructs the file path for a given session ID."""
        return self.session_dir / f"session_{session_id}.json"

    def start_new_session(self) -> str:
        """Generates a new, unique session ID."""
        return str(uuid.uuid4())

    def update_history(
        self, 
        history: List[Dict[str, Any]], 
        role: str, 
        content: str
    ) -> List[Dict[str, Any]]:
        """Appends a new message to the history."""
        history.append({"role": role, "content": content})
        return history

    def load_session(self, session_id: str) -> Optional[List[Dict[str, Any]]]:
        """Loads a session with enhanced integrity checking, sanitization, and recovery."""
        session_path = self._get_session_path(session_id)
        
        if not session_path.exists():
            print(f"ℹ️  Session {session_id} not found. Starting fresh.")
            return []
        
        # Check file size for basic sanity before reading into memory
        try:
            file_size = session_path.stat().st_size
            if file_size > 10 * 1024 * 1024:  # 10MB limit
                print(f"⚠️  Warning: Session file {session_id} is unusually large ({file_size} bytes). Backing up and starting fresh.")
                backup_path = session_path.with_suffix('.json.large_backup')
                session_path.rename(backup_path)
                return []
        except OSError as e:
            print(f"❌ Error: Cannot access session file stats for {session_id}: {e}")
            return None
        
        try:
            with open(session_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                raise ValueError("Session data is not a list.")
            
            # Limit conversation history length to prevent performance degradation
            if len(data) > 1000:
                print(f"⚠️  Warning: Session {session_id} has excessive entries ({len(data)}). Truncating to last 1000.")
                data = data[-1000:]
            
            # Validate and sanitize individual entries
            valid_history = []
            is_dirty = False
            for i, entry in enumerate(data):
                if not (isinstance(entry, dict) and 'role' in entry and 'content' in entry):
                    print(f"⚠️  Warning: Skipping malformed entry at index {i} in session {session_id}.")
                    is_dirty = True
                    continue
                
                # Sanitize content length to prevent memory issues
                if isinstance(entry['content'], str) and len(entry['content']) > 50000:
                    entry['content'] = entry['content'][:50000] + "... [truncated due to excessive length]"
                    is_dirty = True
                
                valid_history.append(entry)
            
            # If we had to clean the session, save the cleaned version back to disk
            if is_dirty:
                print(f"ℹ️  Session {session_id} was sanitized. Saving cleaned version.")
                self.save_session(session_id, valid_history)
            
            print(f"✅ Loaded session {session_id} with {len(valid_history)} valid entries.")
            return valid_history
            
        except (json.JSONDecodeError, ValueError) as e:
            print(f"❌ Error: Session {session_id} is corrupted or has invalid format: {e}")
            backup_path = session_path.with_suffix('.json.corrupted')
            try:
                session_path.rename(backup_path)
                print(f"💾 Corrupted session backed up to: {backup_path}")
            except OSError as backup_e:
                print(f"❌ Error: Could not create backup of corrupted session: {backup_e}")
            return []
            
        except Exception as e:
            print(f"❌ Error: An unexpected error occurred while loading session {session_id}: {e}")
            return None

    def save_session(self, session_id: str, history: List[Dict[str, Any]]):
        """Saves the conversation history with atomic write and backup."""
        session_path = self._get_session_path(session_id)
        temp_path = session_path.with_suffix('.tmp')
        
        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
            
            # Atomically replace the old session file with the new one
            temp_path.replace(session_path)
            
        except IOError as e:
            print(f"❌ ERROR: Could not save session {session_id}: {e}")
            if temp_path.exists():
                temp_path.unlink()