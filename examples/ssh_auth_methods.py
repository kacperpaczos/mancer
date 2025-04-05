#!/usr/bin/env python3
"""
Example of using different SSH authentication methods in the mancer library.
"""

from mancer.application.shell_runner import ShellRunner
from mancer.domain.model.command_result import CommandResult

def print_auth_example(title: str, result: CommandResult):
    """Displays the result of an authentication example"""
    print(f"{title}")
    if result.is_success():
        print(f"Result: {result.raw_output}")
    else:
        print(f"Error: {result.error_message}")

def main():
    # Initialize runner
    runner = ShellRunner(backend_type="bash")
    
    print("=== Examples of different SSH authentication methods ===\n")
    
    # Create hostname command for testing
    hostname_cmd = runner.create_command("hostname")
    
    # 1. Authentication using password
    print("1. Authentication using password")
    # Simulate SSH connection - in reality executed locally
    runner.set_remote_execution(
        host="localhost",
        user="testuser",
        password="password123",
    )
    
    try:
        # Example command
        result = runner.execute(hostname_cmd)
        print_auth_example("Result:", result)
    except Exception as e:
        print(f"Error: {e}")
    
    # 2. Authentication using private key
    print("\n2. Authentication using private key")
    runner.set_remote_execution(
        host="localhost",
        user="testuser",
        key_file="~/.ssh/id_rsa",
    )
    
    try:
        result = runner.execute(hostname_cmd)
        print_auth_example("Result:", result)
    except Exception as e:
        print(f"Error: {e}")
    
    # 3. Authentication using SSH agent
    print("\n3. Authentication using SSH agent")
    runner.set_remote_execution(
        host="localhost",
        user="testuser",
        use_agent=True,
    )
    
    try:
        result = runner.execute(hostname_cmd)
        print_auth_example("Result:", result)
    except Exception as e:
        print(f"Error: {e}")
    
    # 4. Authentication using SSH certificate
    print("\n4. Authentication using SSH certificate")
    runner.set_remote_execution(
        host="localhost",
        user="testuser",
        certificate_file="~/.ssh/id_rsa-cert.pub",
    )
    
    try:
        result = runner.execute(hostname_cmd)
        print_auth_example("Result:", result)
    except Exception as e:
        print(f"Error: {e}")
    
    # 5. GSSAPI Authentication (Kerberos)
    print("\n5. GSSAPI Authentication (Kerberos)")
    runner.set_remote_execution(
        host="localhost",
        user="testuser",
        gssapi_auth=True,
        gssapi_delegate_creds=True,
    )
    
    try:
        result = runner.execute(hostname_cmd)
        print_auth_example("Result:", result)
    except Exception as e:
        print(f"Error: {e}")
    
    # 6. Authentication with custom SSH options
    print("\n6. Authentication with custom SSH options")
    runner.set_remote_execution(
        host="localhost",
        user="testuser",
        ssh_options={
            "PubkeyAuthentication": "yes",
            "PreferredAuthentications": "publickey,password",
            "ConnectTimeout": "10",
            "ServerAliveInterval": "60",
            "ServerAliveCountMax": "3",
        }
    )
    
    try:
        result = runner.execute(hostname_cmd)
        print_auth_example("Result:", result)
    except Exception as e:
        print(f"Error: {e}")
    
    # 7. Combination of different authentication methods
    print("\n7. Combination of different authentication methods")
    runner.set_remote_execution(
        host="localhost",
        user="testuser",
        key_file="~/.ssh/id_rsa",
        use_agent=True,
        identity_only=True,
        ssh_options={
            "PreferredAuthentications": "publickey",
            "ConnectTimeout": "5",
        }
    )
    
    try:
        result = runner.execute(hostname_cmd)
        print_auth_example("Result:", result)
    except Exception as e:
        print(f"Error: {e}")
    
    # Restore local mode
    runner.set_local_execution()
    print("\n8. Local execution (without SSH)")
    result = runner.execute(hostname_cmd)
    print_auth_example("Result:", result)

if __name__ == "__main__":
    main() 