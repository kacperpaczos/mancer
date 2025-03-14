import subprocess
import shlex
import os
import tempfile
from typing import Dict, List, Any, Optional
from ...domain.interface.backend_interface import BackendInterface
from ...domain.model.command_result import CommandResult

class SshBackend(BackendInterface):
    """Backend wykonujący komendy przez SSH na zdalnym hoście"""
    
    def __init__(self, host: str, user: Optional[str] = None, port: int = 22, 
                key_file: Optional[str] = None, password: Optional[str] = None,
                use_sudo: bool = False, sudo_password: Optional[str] = None,
                use_agent: bool = False, certificate_file: Optional[str] = None,
                identity_only: bool = False, gssapi_auth: bool = False,
                gssapi_keyex: bool = False, gssapi_delegate_creds: bool = False,
                ssh_options: Optional[Dict[str, str]] = None):
        """
        Inicjalizuje backend SSH
        
        Args:
            host: Nazwa hosta lub adres IP zdalnego serwera
            user: Nazwa użytkownika (opcjonalnie)
            port: Port SSH (domyślnie 22)
            key_file: Ścieżka do pliku klucza prywatnego (opcjonalnie)
            password: Hasło (opcjonalnie, niezalecane - lepiej używać kluczy)
            use_sudo: Czy automatycznie używać sudo dla komend, które tego wymagają
            sudo_password: Hasło do sudo (opcjonalnie)
            use_agent: Czy używać agenta SSH do uwierzytelniania
            certificate_file: Ścieżka do pliku certyfikatu SSH
            identity_only: Czy używać tylko podanego klucza/certyfikatu (IdentitiesOnly=yes)
            gssapi_auth: Czy używać uwierzytelniania GSSAPI (Kerberos)
            gssapi_keyex: Czy używać wymiany kluczy GSSAPI
            gssapi_delegate_creds: Czy delegować poświadczenia GSSAPI
            ssh_options: Dodatkowe opcje SSH jako słownik
        """
        self.host = host
        self.user = user
        self.port = port
        self.key_file = key_file
        self.password = password
        self.use_sudo = use_sudo
        self.sudo_password = sudo_password
        self.use_agent = use_agent
        self.certificate_file = certificate_file
        self.identity_only = identity_only
        self.gssapi_auth = gssapi_auth
        self.gssapi_keyex = gssapi_keyex
        self.gssapi_delegate_creds = gssapi_delegate_creds
        self.ssh_options = ssh_options or {}
    
    def execute_command(self, command: str, working_dir: Optional[str] = None, 
                       env_vars: Optional[Dict[str, str]] = None,
                       force_sudo: bool = False) -> CommandResult:
        """Wykonuje komendę przez SSH na zdalnym hoście"""
        try:
            # Budujemy komendę SSH
            ssh_command = ["ssh"]
            
            # Dodajemy opcje SSH
            if self.port != 22:
                ssh_command.extend(["-p", str(self.port)])
            
            # Obsługa różnych metod uwierzytelniania
            
            # 1. Klucz prywatny
            if self.key_file:
                ssh_command.extend(["-i", self.key_file])
            
            # 2. Certyfikat SSH
            if self.certificate_file:
                ssh_command.extend(["-i", self.certificate_file])
            
            # 3. Używanie tylko podanych tożsamości
            if self.identity_only:
                ssh_command.extend(["-o", "IdentitiesOnly=yes"])
            
            # 4. Agent SSH
            if self.use_agent:
                ssh_command.extend(["-o", "ForwardAgent=yes"])
            
            # 5. Uwierzytelnianie GSSAPI (Kerberos)
            if self.gssapi_auth:
                ssh_command.extend(["-o", "GSSAPIAuthentication=yes"])
            
            if self.gssapi_keyex:
                ssh_command.extend(["-o", "GSSAPIKeyExchange=yes"])
            
            if self.gssapi_delegate_creds:
                ssh_command.extend(["-o", "GSSAPIDelegateCredentials=yes"])
            
            # Dodajemy opcje dla automatycznego odpowiadania na pytania (non-interactive)
            ssh_command.extend(["-o", "BatchMode=no"])
            ssh_command.extend(["-o", "StrictHostKeyChecking=no"])
            
            # Dodajemy dodatkowe opcje SSH
            for key, value in self.ssh_options.items():
                ssh_command.extend(["-o", f"{key}={value}"])
            
            # Dodajemy użytkownika i hosta
            target = self.host
            if self.user:
                target = f"{self.user}@{self.host}"
            
            ssh_command.append(target)
            
            # Przygotowanie środowiska
            env_prefix = ""
            if env_vars:
                env_parts = []
                for key, value in env_vars.items():
                    env_parts.append(f"export {key}={shlex.quote(value)}")
                if env_parts:
                    env_prefix = "; ".join(env_parts) + "; "
            
            # Przygotowanie katalogu roboczego
            cd_prefix = ""
            if working_dir:
                cd_prefix = f"cd {shlex.quote(working_dir)} && "
            
            # Sprawdzamy, czy używać sudo
            use_sudo_for_command = force_sudo or self.use_sudo
            
            # Łączymy wszystko w jedną komendę
            remote_command = f"{env_prefix}{cd_prefix}{command}"
            
            # Jeśli używamy sudo, dodajemy je do komendy
            if use_sudo_for_command:
                # Jeśli mamy hasło do sudo, używamy go
                if self.sudo_password:
                    # Używamy echo i pipe do sudo -S (czytaj hasło ze standardowego wejścia)
                    remote_command = f"echo {shlex.quote(self.sudo_password)} | sudo -S {remote_command}"
                else:
                    # Bez hasła, po prostu używamy sudo
                    remote_command = f"sudo {remote_command}"
            
            # Dodajemy komendę do wykonania na zdalnym hoście
            ssh_command.append(remote_command)
            
            # Jeśli mamy hasło do SSH, musimy użyć sshpass
            if self.password:
                # Używamy sshpass do podania hasła
                final_command = ["sshpass", "-p", self.password]
                final_command.extend(ssh_command)
            else:
                final_command = ssh_command
            
            # Wykonanie komendy
            process = subprocess.run(
                final_command,
                text=True,
                capture_output=True
            )
            
            # Sprawdzamy, czy komenda nie wymaga sudo (jeśli nie używaliśmy go wcześniej)
            if not use_sudo_for_command and process.returncode == 1 and "permission denied" in process.stderr.lower():
                # Próbujemy ponownie z sudo
                return self.execute_command(command, working_dir, env_vars, force_sudo=True)
            
            # Parsowanie wyniku
            return self.parse_output(
                command,
                process.stdout,
                process.returncode,
                process.stderr
            )
            
        except Exception as e:
            # Obsługa błędów
            return CommandResult(
                raw_output="",
                success=False,
                structured_output=[],
                exit_code=-1,
                error_message=f"Błąd SSH: {str(e)}"
            )
    
    def parse_output(self, command: str, raw_output: str, exit_code: int, 
                    error_output: str = "") -> CommandResult:
        """Parsuje wyjście komendy do standardowego formatu"""
        # Domyślnie zwracamy sukces, jeśli kod wyjścia jest 0
        success = exit_code == 0
        
        # Próbujemy podstawowe strukturyzowanie wyniku (linie tekstu)
        structured_output = []
        if raw_output:
            structured_output = raw_output.strip().split('\n')
            # Usuwamy puste linie
            structured_output = [line for line in structured_output if line]
        
        return CommandResult(
            raw_output=raw_output,
            success=success,
            structured_output=structured_output,
            exit_code=exit_code,
            error_message=error_output if not success else None
        )
    
    def build_command_string(self, command_name: str, options: List[str], 
                           params: Dict[str, Any], flags: List[str]) -> str:
        """Buduje string komendy zgodny z bashem (używanym przez SSH)"""
        parts = [command_name]
        
        # Opcje (krótkie, np. -l)
        parts.extend(options)
        
        # Flagi (długie, np. --recursive)
        parts.extend(flags)
        
        # Parametry (--name=value lub -n value)
        for name, value in params.items():
            if len(name) == 1:
                # Krótka opcja
                parts.append(f"-{name}")
                parts.append(shlex.quote(str(value)))
            else:
                # Długa opcja
                parts.append(f"--{name}={shlex.quote(str(value))}")
        
        return " ".join(parts) 