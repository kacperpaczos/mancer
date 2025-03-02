import os
import subprocess
from typing import Optional, List, Union, Dict
from pathlib import Path
from ..proficer.main import Proficer

class Syncer:
    def __init__(self, proficer: Optional[Proficer] = None):
        self.proficer = proficer or Proficer()
        self.current_connection = None
    
    def connect(self, profile_name: str = "default") -> None:
        """Set active connection based on profile."""
        self.current_connection = self.proficer.load_profile(profile_name)
    
    def _get_connection_string(self) -> str:
        """Generate SSH connection string based on current profile."""
        if not self.current_connection:
            raise RuntimeError("No active connection. Use connect() method first.")
            
        conn = self.current_connection["connection"]
        return f"{conn['username']}@{conn['host']}"
    
    def _run_command(self, command: List[str]) -> subprocess.CompletedProcess:
        """Execute system command with error handling."""
        try:
            return subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Command execution error: {e.stderr}")
    
    def send_file(self, local_path: Union[str, Path], remote_path: str) -> None:
        """Send file to remote server using SCP."""
        conn = self._get_connection_string()
        command = [
            "scp",
            "-P", str(self.current_connection["connection"]["port"]),
            str(local_path),
            f"{conn}:{remote_path}"
        ]
        self._run_command(command)
    
    def get_file(self, remote_path: str, local_path: Union[str, Path]) -> None:
        """Download file from remote server using SCP."""
        conn = self._get_connection_string()
        command = [
            "scp",
            "-P", str(self.current_connection["connection"]["port"]),
            f"{conn}:{remote_path}",
            str(local_path)
        ]
        self._run_command(command)
    
    def send_directory(self, local_dir: Union[str, Path], remote_dir: str) -> None:
        """Send directory recursively to remote server."""
        conn = self._get_connection_string()
        command = [
            "scp",
            "-r",  # recursive
            "-P", str(self.current_connection["connection"]["port"]),
            str(local_dir),
            f"{conn}:{remote_dir}"
        ]
        self._run_command(command)
    
    def get_directory(self, remote_dir: str, local_dir: Union[str, Path]) -> None:
        """Download directory recursively from remote server."""
        conn = self._get_connection_string()
        command = [
            "scp",
            "-r",  # recursive
            "-P", str(self.current_connection["connection"]["port"]),
            f"{conn}:{remote_dir}",
            str(local_dir)
        ]
        self._run_command(command)
    
    def find_files(self, remote_path: str, pattern: str = "*") -> List[str]:
        """Search for files on remote server using find."""
        conn = self._get_connection_string()
        command = [
            "ssh",
            "-p", str(self.current_connection["connection"]["port"]),
            conn,
            f"find {remote_path} -name '{pattern}'"
        ]
        result = self._run_command(command)
        return result.stdout.strip().split('\n')
    
    def execute_remote(self, command: str) -> str:
        """Execute command on remote server via SSH."""
        conn = self._get_connection_string()
        ssh_command = [
            "ssh",
            "-p", str(self.current_connection["connection"]["port"]),
            conn,
            command
        ]
        result = self._run_command(ssh_command)
        return result.stdout
    
    def replace_file(self, local_path: Union[str, Path], remote_pattern: str, make_backup: bool = True) -> None:
        """Find and replace file on remote server.
        
        Args:
            local_path: Path to local file to send
            remote_pattern: Pattern to find file on remote server
            make_backup: Whether to create backup before replacement
        """
        # Find files matching pattern
        found_files = self.find_files("/", remote_pattern)
        
        if not found_files or found_files[0] == '':
            raise FileNotFoundError(f"No files found matching pattern: {remote_pattern}")
        
        # Display found files and ask user
        print("Found files:")
        for i, file_path in enumerate(found_files, 1):
            print(f"{i}. {file_path}")
        
        if len(found_files) > 1:
            choice = input("Select file number to replace (0 to cancel): ")
            if not choice.isdigit() or int(choice) == 0:
                print("Operation cancelled.")
                return
            selected_file = found_files[int(choice) - 1]
        else:
            choice = input("Do you want to replace this file? (y/n): ")
            if choice.lower() != 'y':
                print("Operation cancelled.")
                return
            selected_file = found_files[0]
        
        # Create backup
        if make_backup:
            backup_path = f"{selected_file}.bak"
            self.execute_remote(f"cp {selected_file} {backup_path}")
            print(f"Created backup: {backup_path}")
        
        # Send new file
        self.send_file(local_path, selected_file)
        print(f"File has been replaced: {selected_file}")