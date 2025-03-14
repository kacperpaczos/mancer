from mancer.application.shell_runner import ShellRunner
import time
import json

def main():
    # Inicjalizacja runnera z włączonym cache
    runner = ShellRunner(
        backend_type="bash",
        enable_cache=True,
        cache_max_size=200,
        cache_auto_refresh=True,
        cache_refresh_interval=10
    )
    
    print("=== Demonstracja użycia cache w ShellRunner ===\n")
    
    # Tworzenie komend (używamy wszystkich dostępnych komend)
    ls = runner.create_command("ls").long().all()
    ps = runner.create_command("ps").aux()
    hostname = runner.create_command("hostname")
    df = runner.create_command("df").human_readable()
    echo = runner.create_command("echo").text("Hello from cache example!")
    cat = runner.create_command("cat").file("/etc/hostname")
    grep = runner.create_command("grep").pattern("root").file("/etc/passwd")
    tail = runner.create_command("tail").lines(5).file("/var/log/syslog")
    head = runner.create_command("head").lines(5).file("/etc/passwd")
    
    # Wykonanie komendy - wynik zostanie zapisany w cache
    print("Wykonanie komendy 'ls -la':")
    result1 = runner.execute(ls)
    print(f"Status: {'Sukces' if result1.is_success() else 'Błąd'}")
    print(f"Liczba linii wyniku: {len(result1.raw_output.splitlines())}")
    
    # Pobranie statystyk cache
    print("\nStatystyki cache po pierwszym wykonaniu:")
    stats = runner.get_cache_statistics()
    print(json.dumps(stats, indent=2))
    
    # Wykonanie tej samej komendy ponownie - wynik powinien być pobrany z cache
    print("\nWykonanie tej samej komendy ponownie (powinno użyć cache):")
    start_time = time.time()
    result2 = runner.execute(ls)
    end_time = time.time()
    print(f"Czas wykonania: {(end_time - start_time)*1000:.2f} ms")
    print(f"Status: {'Sukces' if result2.is_success() else 'Błąd'}")
    
    # Wykonanie nowych komend
    print("\nWykonanie komendy 'df -h':")
    result3 = runner.execute(df)
    print(f"Status: {'Sukces' if result3.is_success() else 'Błąd'}")
    print(f"Wynik: {result3.raw_output[:200]}...")  # Pokazujemy tylko początek wyniku
    
    print("\nWykonanie komendy 'echo Hello from cache example!':")
    result4 = runner.execute(echo)
    print(f"Status: {'Sukces' if result4.is_success() else 'Błąd'}")
    print(f"Wynik: {result4.raw_output}")
    
    print("\nWykonanie komendy 'cat /etc/hostname':")
    result5 = runner.execute(cat)
    print(f"Status: {'Sukces' if result5.is_success() else 'Błąd'}")
    print(f"Wynik: {result5.raw_output}")
    
    print("\nWykonanie komendy 'head -n 5 /etc/passwd':")
    result_head = runner.execute(head)
    print(f"Status: {'Sukces' if result_head.is_success() else 'Błąd'}")
    print(f"Wynik: {result_head.raw_output}")
    
    # Wykonanie łańcucha komend
    print("\nWykonanie łańcucha komend 'ls -la | grep py':")
    grep_py = runner.create_command("grep").pattern("py")
    chain = ls.pipe(grep_py)
    result6 = runner.execute(chain)
    print(f"Status: {'Sukces' if result6.is_success() else 'Błąd'}")
    print(f"Wynik: {result6.raw_output}")
    
    # Pobranie historii wykonanych komend
    print("\nHistoria wykonanych komend:")
    history = runner.get_command_history()
    for i, (cmd_id, timestamp, success) in enumerate(history):
        print(f"{i+1}. ID: {cmd_id[:8]}... | Czas: {timestamp} | Status: {'Sukces' if success else 'Błąd'}")
    
    # Eksport danych cache do JSON
    print("\nEksport danych cache (bez wyników):")
    cache_data = runner.export_cache_data(include_results=False)
    print(json.dumps(cache_data, indent=2, default=str)[:500] + "...")
    
    # Demonstracja czyszczenia cache
    print("\nCzyszczenie cache...")
    runner.clear_cache()
    print("Statystyki po wyczyszczeniu:")
    stats = runner.get_cache_statistics()
    print(json.dumps(stats, indent=2))
    
    # Demonstracja wyłączania i włączania cache
    print("\nWyłączanie cache...")
    runner.disable_cache()
    
    print("Wykonanie komendy z wyłączonym cache:")
    result7 = runner.execute(ls)
    print(f"Status: {'Sukces' if result7.is_success() else 'Błąd'}")
    
    print("\nWłączanie cache ponownie...")
    runner.enable_cache(auto_refresh=False)
    
    print("Wykonanie komendy z włączonym cache:")
    result8 = runner.execute(ls)
    print(f"Status: {'Sukces' if result8.is_success() else 'Błąd'}")
    
    # Pobranie statystyk cache
    print("\nStatystyki cache na koniec:")
    stats = runner.get_cache_statistics()
    print(json.dumps(stats, indent=2))

if __name__ == "__main__":
    main() 