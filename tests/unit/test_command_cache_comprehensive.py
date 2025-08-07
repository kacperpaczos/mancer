"""
Kompleksowe testy dla CommandCache - zwiększenie pokrycia do 85%+
"""
import pytest
import time
import threading
from datetime import datetime
from unittest.mock import Mock, patch

from mancer.application.command_cache import CommandCache
from mancer.domain.model.command_result import CommandResult


class TestCommandCacheComprehensive:
    """Kompleksowe testy CommandCache"""
    
    def setup_method(self):
        """Setup przed każdym testem"""
        self.cache = CommandCache(max_size=5)
        
        # Przykładowy CommandResult do testów
        self.sample_result = CommandResult(
            raw_output="test output",
            success=True,
            structured_output=["test", "output"],
            exit_code=0
        )
    
    def test_cache_initialization_basic(self):
        """Test podstawowej inicjalizacji cache"""
        cache = CommandCache()
        
        assert cache._max_size == 100  # domyślny rozmiar
        assert cache._auto_refresh == False
        assert cache._refresh_interval == 5
        assert len(cache._cache) == 0
        assert len(cache._history) == 0
        assert cache._refresh_thread is None
    
    def test_cache_initialization_with_auto_refresh(self):
        """Test inicjalizacji cache z auto-refresh"""
        cache = CommandCache(max_size=10, auto_refresh=True, refresh_interval=2)
        
        assert cache._max_size == 10
        assert cache._auto_refresh == True
        assert cache._refresh_interval == 2
        assert cache._refresh_thread is not None
        assert cache._refresh_thread.daemon == True
        
        # Cleanup
        cache.clear()
    
    def test_store_and_get_basic(self):
        """Test podstawowego dodawania i pobierania z cache"""
        command_id = "test_cmd_1"
        command_str = "echo test"

        self.cache.store(command_id, command_str, self.sample_result)
        retrieved = self.cache.get(command_id)

        assert retrieved is not None
        assert retrieved.raw_output == "test output"
        assert retrieved.success == True
        assert len(self.cache._history) == 1

    def test_store_with_metadata(self):
        """Test dodawania z metadanymi"""
        command_id = "test_cmd_meta"
        command_str = "echo meta"
        metadata = {"execution_time": 1.5, "user": "test_user"}

        self.cache.store(command_id, command_str, self.sample_result, metadata)
        result_with_meta = self.cache.get_with_metadata(command_id)

        assert result_with_meta is not None
        result, timestamp, meta = result_with_meta
        assert result.raw_output == "test output"
        assert isinstance(timestamp, datetime)
        assert meta["metadata"]["execution_time"] == 1.5
        assert meta["metadata"]["user"] == "test_user"
    
    def test_get_nonexistent(self):
        """Test pobierania nieistniejącego wpisu"""
        result = self.cache.get("nonexistent")
        assert result is None
        
        result_with_meta = self.cache.get_with_metadata("nonexistent")
        assert result_with_meta is None
    
    def test_cache_size_limit(self):
        """Test limitu rozmiaru cache"""
        # Dodaj więcej elementów niż max_size (5)
        for i in range(7):
            cmd_id = f"cmd_{i}"
            result = CommandResult(
                raw_output=f"output_{i}",
                success=True,
                structured_output=[f"output_{i}"],
                exit_code=0
            )
            self.cache.store(cmd_id, f"echo {i}", result)
        
        # Cache powinien mieć maksymalnie 5 elementów
        assert len(self.cache._cache) == 5
        assert len(self.cache._history) == 5
        
        # Najstarsze elementy powinny być usunięte
        assert self.cache.get("cmd_0") is None
        assert self.cache.get("cmd_1") is None
        assert self.cache.get("cmd_6") is not None
    
    def test_get_history_basic(self):
        """Test pobierania historii"""
        # Dodaj kilka komend
        for i in range(3):
            cmd_id = f"hist_cmd_{i}"
            result = CommandResult(
                raw_output=f"output_{i}",
                success=i % 2 == 0,  # co druga komenda successful
                structured_output=[f"output_{i}"],
                exit_code=0 if i % 2 == 0 else 1
            )
            self.cache.store(cmd_id, f"echo {i}", result)
        
        history = self.cache.get_history()
        assert len(history) == 3
        
        # Sprawdź format historii
        for entry in history:
            assert len(entry) == 3  # (command_id, timestamp, success)
            assert isinstance(entry[1], datetime)
            assert isinstance(entry[2], bool)
    
    def test_get_history_with_limit(self):
        """Test pobierania historii z limitem"""
        # Dodaj 5 komend
        for i in range(5):
            cmd_id = f"limit_cmd_{i}"
            self.cache.store(cmd_id, f"echo limit_{i}", self.sample_result)
        
        history = self.cache.get_history(limit=3)
        assert len(history) == 3
        
        # Powinny być najnowsze wpisy (od końca)
        assert "limit_cmd_4" in history[-1][0]
    
    def test_get_history_success_only(self):
        """Test pobierania tylko udanych komend z historii"""
        # Dodaj komendy z różnymi statusami
        for i in range(4):
            cmd_id = f"success_cmd_{i}"
            result = CommandResult(
                raw_output=f"output_{i}",
                success=i % 2 == 0,  # 0,2 = success, 1,3 = failure
                structured_output=[f"output_{i}"],
                exit_code=0 if i % 2 == 0 else 1
            )
            self.cache.store(cmd_id, f"cmd_{cmd_id}", result)
        
        all_history = self.cache.get_history()
        success_history = self.cache.get_history(success_only=True)
        
        assert len(all_history) == 4
        assert len(success_history) == 2  # tylko success_cmd_0 i success_cmd_2
        
        for entry in success_history:
            assert entry[2] == True  # wszystkie successful
    
    def test_clear_cache(self):
        """Test czyszczenia cache"""
        # Dodaj kilka elementów
        for i in range(3):
            self.cache.store(f"clear_cmd_{i}", f"echo clear_{i}", self.sample_result)
        
        assert len(self.cache._cache) == 3
        assert len(self.cache._history) == 3
        
        self.cache.clear()
        
        assert len(self.cache._cache) == 0
        assert len(self.cache._history) == 0
    
    def test_get_statistics(self):
        """Test pobierania statystyk cache"""
        # Dodaj komendy z różnymi statusami
        for i in range(5):
            cmd_id = f"stats_cmd_{i}"
            result = CommandResult(
                raw_output=f"output_{i}",
                success=i < 3,  # pierwsze 3 successful, ostatnie 2 failed
                structured_output=[f"output_{i}"],
                exit_code=0 if i < 3 else 1
            )
            self.cache.store(cmd_id, f"cmd_{cmd_id}", result)
        
        stats = self.cache.get_statistics()
        
        assert stats["total_commands"] == 5
        assert stats["success_count"] == 3
        assert stats["error_count"] == 2
        assert stats["cache_size"] == 5
        assert stats["max_size"] == 5
        assert stats["auto_refresh"] == False
        assert stats["refresh_interval"] == 5
    
    def test_threading_safety(self):
        """Test bezpieczeństwa wątkowego"""
        results = []
        
        def add_to_cache(thread_id):
            for i in range(10):
                cmd_id = f"thread_{thread_id}_cmd_{i}"
                result = CommandResult(
                    raw_output=f"thread_{thread_id}_output_{i}",
                    success=True,
                    structured_output=[f"output_{i}"],
                    exit_code=0
                )
                self.cache.store(cmd_id, f"cmd_{cmd_id}", result)
                results.append(cmd_id)
        
        # Uruchom 3 wątki jednocześnie
        threads = []
        for t in range(3):
            thread = threading.Thread(target=add_to_cache, args=(t,))
            threads.append(thread)
            thread.start()
        
        # Poczekaj na zakończenie wszystkich wątków
        for thread in threads:
            thread.join()
        
        # Cache powinien mieć maksymalnie max_size elementów
        assert len(self.cache._cache) <= self.cache._max_size
        assert len(self.cache._history) <= self.cache._max_size
    
    @patch('time.sleep')
    def test_refresh_loop(self, mock_sleep):
        """Test pętli odświeżającej cache"""
        cache = CommandCache(auto_refresh=True, refresh_interval=1)
        
        # Poczekaj chwilę żeby wątek się uruchomił
        time.sleep(0.1)
        
        # Zatrzymaj refresh
        cache._stop_refresh.set()
        
        # Sprawdź czy wątek był aktywny
        assert cache._refresh_thread is not None
        
        # Cleanup
        cache.clear()
    
    def test_auto_refresh_cleanup(self):
        """Test że clear() nie zatrzymuje refresh thread (tylko czyści dane)"""
        cache = CommandCache(auto_refresh=True, refresh_interval=1)

        assert cache._refresh_thread is not None
        assert not cache._stop_refresh.is_set()

        cache.clear()

        # clear() nie zatrzymuje refresh thread, tylko czyści dane
        assert not cache._stop_refresh.is_set()
        assert cache._refresh_thread is not None

        # Zatrzymaj ręcznie dla cleanup
        cache.stop_refresh()

    def test_set_auto_refresh_enable(self):
        """Test włączania auto-refresh"""
        cache = CommandCache(auto_refresh=False)

        assert cache._auto_refresh == False
        assert cache._refresh_thread is None

        cache.set_auto_refresh(True, interval=3)

        assert cache._auto_refresh == True
        assert cache._refresh_interval == 3
        assert cache._refresh_thread is not None

        # Cleanup
        cache.clear()

    def test_set_auto_refresh_disable(self):
        """Test wyłączania auto-refresh"""
        cache = CommandCache(auto_refresh=True, refresh_interval=1)

        assert cache._auto_refresh == True
        assert cache._refresh_thread is not None

        cache.set_auto_refresh(False)

        assert cache._auto_refresh == False
        # Wątek powinien zostać zatrzymany

        # Cleanup
        cache.clear()

    def test_stop_refresh(self):
        """Test zatrzymywania refresh thread"""
        cache = CommandCache(auto_refresh=True, refresh_interval=1)

        assert cache._refresh_thread is not None
        assert cache._refresh_thread.is_alive()

        cache.stop_refresh()

        # Poczekaj chwilę na zatrzymanie wątku
        time.sleep(0.1)
        assert cache._stop_refresh.is_set()

    def test_export_data_without_results(self):
        """Test eksportu danych bez wyników"""
        # Dodaj kilka komend
        for i in range(3):
            cmd_id = f"export_cmd_{i}"
            result = CommandResult(
                raw_output=f"output_{i}",
                success=i % 2 == 0,
                structured_output=[f"output_{i}"],
                exit_code=0 if i % 2 == 0 else 1
            )
            self.cache.store(cmd_id, f"cmd_{cmd_id}", result)

        export = self.cache.export_data(include_results=False)

        assert "history" in export
        assert "statistics" in export
        assert "results" not in export

        assert len(export["history"]) == 3
        assert export["statistics"]["total_commands"] == 3

    def test_export_data_with_results(self):
        """Test eksportu danych z wynikami"""
        cmd_id = "export_with_results"
        metadata = {"test_meta": "value"}

        self.cache.store(cmd_id, "echo export", self.sample_result, metadata)

        export = self.cache.export_data(include_results=True)

        assert "history" in export
        assert "statistics" in export
        assert "results" in export

        assert cmd_id in export["results"]
        result_data = export["results"][cmd_id]

        assert result_data["success"] == True
        assert result_data["exit_code"] == 0
        assert result_data["raw_output"] == "test output"
        assert result_data["structured_output"] == ["test", "output"]
        assert result_data["metadata"]["metadata"]["test_meta"] == "value"
        assert "timestamp" in result_data

    def test_len_method(self):
        """Test metody __len__"""
        assert len(self.cache) == 0

        self.cache.store("test1", "echo test1", self.sample_result)
        assert len(self.cache) == 1

        self.cache.store("test2", "echo test2", self.sample_result)
        assert len(self.cache) == 2

        self.cache.clear()
        assert len(self.cache) == 0

    def test_cache_overflow_history_consistency(self):
        """Test spójności historii przy przepełnieniu cache"""
        # Dodaj więcej elementów niż max_size
        for i in range(8):
            cmd_id = f"overflow_cmd_{i}"
            result = CommandResult(
                raw_output=f"output_{i}",
                success=True,
                structured_output=[f"output_{i}"],
                exit_code=0
            )
            self.cache.store(cmd_id, f"cmd_{cmd_id}", result)

        # Cache i historia powinny mieć tę samą długość
        assert len(self.cache._cache) == len(self.cache._history)
        assert len(self.cache._cache) == self.cache._max_size

        # Najstarsze wpisy powinny być usunięte z obu struktur
        assert "overflow_cmd_0" not in self.cache._cache
        assert "overflow_cmd_7" in self.cache._cache
