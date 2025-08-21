from mancer.application.shell_runner import ShellRunner


def main():
    # Initialize runner
    runner = ShellRunner(backend_type="bash")

    # Local execution example
    print("=== Local Execution ===")
    ls = runner.create_command("ls").long().all()
    result = runner.execute(ls)
    print("Local ls result:")
    print(result.raw_output)

    # Remote execution configuration with password
    print("\n=== Remote Execution Configuration with Password ===")
    runner.set_remote_execution(
        host="example.com",  # Change to proper host
        user="username",  # Change to proper username
        password="password123",  # Change to proper password
        # port=22,               # Optional, default is 22
        # key_file="~/.ssh/id_rsa"  # Optional, path to key file
    )

    # Remote execution example with password
    print("\n=== Remote Execution with Password ===")
    remote_ls = runner.create_command("ls").long().all()
    try:
        remote_result = runner.execute(remote_ls)
        print("Remote ls result:")
        print(remote_result.raw_output)
    except Exception as e:
        print(f"Remote execution error: {e}")

    # Remote execution configuration with sudo
    print("\n=== Remote Execution Configuration with Sudo ===")
    runner.set_remote_execution(
        host="example.com",  # Change to proper host
        user="username",  # Change to proper username
        password="password123",  # Change to proper password
        use_sudo=True,  # Use sudo automatically when needed
        sudo_password="sudo_password123",  # Change to proper sudo password
    )

    # Remote execution example with sudo
    print("\n=== Remote Execution with Sudo ===")
    # Command that requires root privileges
    remote_apt = runner.create_command("apt").with_param("update", "")
    try:
        apt_result = runner.execute(remote_apt)
        print("Remote apt update result with sudo:")
        print(
            apt_result.raw_output[:200] + "..."
            if len(apt_result.raw_output) > 200
            else apt_result.raw_output
        )
    except Exception as e:
        print(f"Remote execution error with sudo: {e}")

    # Example of explicitly marking a command as requiring sudo
    print("\n=== Execution of Command Explicitly Marked as Requiring Sudo ===")
    # Command that we explicitly mark as requiring sudo
    remote_service = runner.create_command("systemctl").with_param("status", "nginx").with_sudo()
    try:
        service_result = runner.execute(remote_service)
        print("Remote systemctl status nginx result with sudo:")
        print(
            service_result.raw_output[:200] + "..."
            if len(service_result.raw_output) > 200
            else service_result.raw_output
        )
    except Exception as e:
        print(f"Remote execution error with sudo: {e}")

    # Example of automatic detection of sudo need
    print("\n=== Automatic Detection of Sudo Need ===")
    # Configuration with automatic sudo, but without explicit command marking
    runner.set_remote_execution(
        host="example.com",  # Change to proper host
        user="username",  # Change to proper username
        password="password123",  # Change to proper password
        use_sudo=True,  # Use sudo automatically when needed
        sudo_password="sudo_password123",  # Change to proper sudo password
    )

    # Command that may require sudo, but is not explicitly marked
    remote_cat = runner.create_command("cat").with_param("path", "/var/log/syslog")
    try:
        cat_result = runner.execute(remote_cat)
        print("Remote cat /var/log/syslog result (automatic sudo if needed):")
        print(
            cat_result.raw_output[:200] + "..."
            if len(cat_result.raw_output) > 200
            else cat_result.raw_output
        )
    except Exception as e:
        print(f"Remote execution error: {e}")


if __name__ == "__main__":
    main()
