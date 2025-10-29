import json
import time

from mancer.application.shell_runner import ShellRunner


def main():
    # Initialize runner with cache enabled
    runner = ShellRunner(
        backend_type="bash",
        enable_cache=True,
        cache_max_size=200,
        cache_auto_refresh=True,
        cache_refresh_interval=10,
    )

    print("=== Cache Usage Demonstration in ShellRunner ===\n")

    # Creating commands (using all available commands)
    ls = runner.create_command("ls").long().all()
    ps = runner.create_command("ps").aux()
    hostname = runner.create_command("hostname").fqdn()
    df = runner.create_command("df").human_readable()
    echo = runner.create_command("echo").text("Hello from cache example!")
    cat = runner.create_command("cat").file("/etc/hostname")
    grep = runner.create_command("grep").pattern("root").file("/etc/passwd")
    tail = runner.create_command("tail").lines(5).file("/var/log/syslog")
    head = runner.create_command("head").lines(5).file("/etc/passwd")

    # Execute command - result will be saved in cache
    print("Executing 'ls -la' command:")
    result1 = runner.execute(ls)
    print(f"Status: {'Success' if result1.success else 'Error'}")
    print(f"Number of result lines: {len(result1.raw_output.splitlines())}")

    # Get cache statistics
    print("\nCache statistics after first execution:")
    stats = runner.get_cache_statistics()
    print(json.dumps(stats, indent=2))

    # Execute the same command again - result should be retrieved from cache
    print("\nExecuting the same command again (should use cache):")
    start_time = time.time()
    result2 = runner.execute(ls)
    end_time = time.time()
    print(f"Execution time: {(end_time - start_time)*1000:.2f} ms")
    print(f"Status: {'Success' if result2.success else 'Error'}")

    # Execute new commands
    print("\nExecuting 'df -h' command:")
    result3 = runner.execute(df)
    print(f"Status: {'Success' if result3.success else 'Error'}")
    print(f"Result: {result3.raw_output[:200]}...")  # Showing only the beginning of the result

    print("\nExecuting 'echo Hello from cache example!' command:")
    result4 = runner.execute(echo)
    print(f"Status: {'Success' if result4.success else 'Error'}")
    print(f"Result: {result4.raw_output}")

    print("\nExecuting 'cat /etc/hostname' command:")
    result5 = runner.execute(cat)
    print(f"Status: {'Success' if result5.success else 'Error'}")
    print(f"Result: {result5.raw_output}")

    print("\nExecuting 'head -n 5 /etc/passwd' command:")
    result_head = runner.execute(head)
    print(f"Status: {'Success' if result_head.success else 'Error'}")
    print(f"Result: {result_head.raw_output}")

    # Execute command chain
    print("\nExecuting command chain 'ls -la | grep py':")
    grep_py = runner.create_command("grep").pattern("py")
    chain = ls.pipe(grep_py)
    result6 = runner.execute(chain)
    print(f"Status: {'Success' if result6.success else 'Error'}")
    print(f"Result: {result6.raw_output}")

    # Get history of executed commands
    print("\nHistory of executed commands:")
    history = runner.get_command_history()
    for i, (cmd_id, timestamp, success) in enumerate(history):
        print(f"{i+1}. ID: {cmd_id[:8]}... | Time: {timestamp} | Status: {'Success' if success else 'Error'}")

    # Export cache data to JSON
    print("\nExporting cache data (without results):")
    cache_data = runner.export_cache_data(include_results=False)
    print(json.dumps(cache_data, indent=2, default=str)[:500] + "...")

    # Demonstrate cache clearing
    print("\nClearing cache...")
    runner.clear_cache()
    print("Statistics after clearing:")
    stats = runner.get_cache_statistics()
    print(json.dumps(stats, indent=2))

    # Demonstrate disabling and enabling cache
    print("\nDisabling cache...")
    runner.disable_cache()

    print("Executing command with cache disabled:")
    result7 = runner.execute(ls)
    print(f"Status: {'Success' if result7.success else 'Error'}")

    print("\nEnabling cache again...")
    runner.enable_cache(auto_refresh=False)

    print("Executing command with cache enabled:")
    result8 = runner.execute(ls)
    print(f"Status: {'Success' if result8.success else 'Error'}")

    # Get cache statistics
    print("\nCache statistics at the end:")
    stats = runner.get_cache_statistics()
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
