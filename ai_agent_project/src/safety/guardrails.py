import os
from typing import List
from ai_agent_project.src.core.types import Action

class SecurityError(Exception):
    pass

class SafetyGuardrails:
    def __init__(self, allowed_paths: List[str] = None):
        self.allowed_paths = allowed_paths or [os.getcwd()]
        self.forbidden_commands = ["rm -rf", "sudo", "chmod", "mkfs"]
    
    def validate_action(self, action: Action) -> bool:
        """
        Validates an action before execution. 
        Returns True if safe, raises SecurityError if unsafe.
        """
        tool = action.tool_name
        args = action.tool_args
        
        # 1. File Access Check
        if tool in ["read_file", "write_file"]:
            path = args.get("path") or args.get("file_path")
            if path:
                self._check_path_safety(path)
                
        # 2. Command Safety Check (if we had a shell tool)
        if tool == "run_command":
            cmd = args.get("command", "")
            self._check_command_safety(cmd)
            
        print(f"Safety: Action '{tool}' validated.")
        return True

    def _check_path_safety(self, path: str):
        # Resolve absolute path
        abs_path = os.path.abspath(path)
        
        # Check if path is within allowed directories
        allowed = False
        for safe_dir in self.allowed_paths:
            if os.path.commonpath([safe_dir, abs_path]) == os.path.abspath(safe_dir):
                allowed = True
                break
        
        if not allowed:
            raise SecurityError(f"Access denied: Path '{path}' is outside allowed workspace.")

    def _check_command_safety(self, command: str):
        for bad_cmd in self.forbidden_commands:
            if bad_cmd in command:
                raise SecurityError(f"Command blocked: '{bad_cmd}' is forbidden.")
