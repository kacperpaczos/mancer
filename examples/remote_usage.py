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

    # Remote execution configuration
    # Note: Provide proper SSH connection details
    print("\n=== Remote Execution Configuration ===")
    runner.set_remote_execution(
        host="example.com",  # Change to proper host
        user="username",  # Change to proper username
        # port=22,           # Optional, default is 22
        # key_file="~/.ssh/id_rsa"  # Optional, path to key file
    )

    # Remote execution example
    print("\n=== Remote Execution ===")
    remote_ls = runner.create_command("ls").long().all()
    try:
        remote_result = runner.execute(remote_ls)
        print("Remote ls result:")
        print(remote_result.raw_output)
    except Exception as e:
        print(f"Remote execution error: {e}")

    # Remote command chain example
    print("\n=== Remote Command Chain ===")
    cd = runner.create_command("cd").to_directory("/tmp")
    find = runner.create_command("find").with_name("*.log")

    try:
        chain_result = runner.execute(cd.then(find))
        print('Remote result of cd /tmp | find -name "*.log":')
        print(chain_result.raw_output)
    except Exception as e:
        print(f"Remote chain execution error: {e}")

    # Switch back to local execution
    print("\n=== Switching Back to Local Execution ===")
    runner.set_local_execution()

    local_result = runner.execute(ls)
    print("Local ls result after switching back:")
    print(local_result.raw_output)

    # Mixed execution example - some commands local, some remote
    print("\n=== Mixed Execution (Local/Remote) ===")
    print("Local execution:")
    local_ps = runner.create_command("ps").all()
    local_ps_result = runner.execute(local_ps)
    print(
        local_ps_result.raw_output[:200] + "..."
        if len(local_ps_result.raw_output) > 200
        else local_ps_result.raw_output
    )

    print("\nSwitching to remote:")
    runner.set_remote_execution(
        host="example.com",  # Change to proper host
        user="username",  # Change to proper username
    )

    try:
        remote_ps = runner.create_command("ps").all()
        remote_ps_result = runner.execute(remote_ps)
        print(
            remote_ps_result.raw_output[:200] + "..."
            if len(remote_ps_result.raw_output) > 200
            else remote_ps_result.raw_output
        )
    except Exception as e:
        print(f"Remote execution error: {e}")


if __name__ == "__main__":
    main()
