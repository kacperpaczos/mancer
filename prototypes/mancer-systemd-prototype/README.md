# Mancer Systemd Prototype

**Zaawansowany prototyp do zarządzania systemd z interfejsem TUI, zorientowany na sieć (network-oriented).** Integruje funkcje z istniejących projektów oraz nowoczesne narzędzia TUI, umożliwiając zarządzanie wieloma serwerami systemd przez sieć.

## Funkcje z istniejących projektów

### Z `prototypes/systemctl/`:
- Zarządzanie jednostkami systemd przez SSH
- Pobieranie listy wszystkich jednostek systemd (`systemctl list-units`)
- Zarządzanie usługami (start/stop/restart/enable/disable)
- Generowanie raportów z jednostek systemd
- Integracja z frameworkiem Mancer
- Zarządzanie wieloma serwerami jednocześnie
- Szyfrowanie haseł SSH

### Z `prototypes/sysdch/`:
- Zarządzanie jednostkami systemd przez SSH
- Pobieranie i analiza jednostek systemd
- Zarządzanie konfiguracją systemd (przeładowanie, edycja plików)
- Interaktywny interfejs z Rich (tabele, panele)
- Edycja plików konfiguracyjnych systemd w różnych lokalizacjach:
  - `/etc/systemd/system/`
  - `/usr/lib/systemd/system/`
  - `/run/systemd/system/`
  - `/usr/local/lib/systemd/system/`
- Fuzzy search jednostek
- Zarządzanie konfiguracją systemd

## Nowe funkcje TUI (inspirowane systemctl-tui, systemd-manager-tui, isd, ServiceMaster, sysz)

### Podstawowe zarządzanie:
- **Przeglądanie statusu usług** - lista wszystkich jednostek z kolorowym statusem
- **Podgląd i przeglądanie logów usług** - integracja z journalctl
- **Uruchamianie, zatrzymywanie, restartowanie i przeładowywanie usług**
- **Podgląd i edycja plików jednostek (unit files)** - edytor inline
- **Prosty, szybki i minimalistyczny interfejs** skupiony na kluczowych funkcjach

### Zaawansowane funkcje:
- **Lista usług (systemowych i użytkownika)** - przełączanie między typami
- **Podgląd i filtrowanie usług** wg statusu (active, dead, disabled, failed)
- **Start, stop, restart, enable, disable, mask, unmask** jednostek
- **Fuzzy search (nieliniowe wyszukiwanie)** usług
- **Automatyczne odświeżanie** podglądu jednostek
- **Otwieranie wyników w pagerze lub edytorze**
- **Automatyczne dodawanie sudo**, jeśli wymagane

### Interfejs użytkownika:
- **Kolorowy interfejs ncurses** z klawiszowymi skrótami
- **Szybkie skróty klawiszowe** do nawigacji i kontroli
- **Reakcja na zmiany jednostek w czasie rzeczywistym** przez DBus event loop
- **Skalowalny i konfigurowalny wygląd UI**
- **Rozbudowana paleta poleceń** i skróty klawiszowe
- **Konfigurowalne klawisze, tematy i ustawienia** w pliku YAML z autouzupełnianiem

### Funkcje systemowe:
- **Wyświetlanie wszystkich jednostek systemd** lub filtrowanie po typie
- **Szczegółowy status każdej jednostki** z metadanymi
- **Przełączanie między jednostkami systemowymi a użytkownika**
- **Możliwość wykonania daemon-reload** z klawiatury
- **Skrócone polecenia systemctl** do szybszej obsługi
- **Status automatycznie po wykonaniu komend** typu start, stop, restart
- **Możliwość wyboru wielu jednostek i akcji** (TAB)
- **Dynamiczne podpowiadanie dostępnych akcji** na podstawie stanu jednostki

### **Przykład hybrydowego wyszukiwania:**
```
🔍 Wyszukiwanie: "nginx"
┌─────────────────────────────────────────────────────────────┐
│ 📱 LOKALNY SYSTEM (localhost)                              │
│ ✅ nginx.service - active (running)                        │
│ ✅ nginx.socket - active (listening)                       │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│ 🌐 SERWER PRODUKCYJNY (prod-server-01)                    │
│ ✅ nginx.service - active (running)                        │
│ ⚠️  nginx.socket - inactive (dead)                        │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│ 🌐 SERWER STAGING (staging-server-01)                     │
│ ❌ nginx.service - failed                                  │
│ ❌ nginx.socket - inactive (dead)                          │
└─────────────────────────────────────────────────────────────┘
```

### **Przykład zarządzania grupami Enterprise:**
```
🏢 GRUPA: PRODUKCJA-EUROPA
├── 🌍 Region: Europa Zachodnia
│   ├── 🏭 Data Center: Frankfurt
│   │   ├── 🔧 Environment: Production
│   │   │   ├── 📡 prod-frankfurt-01 (✅ Healthy)
│   │   │   ├── 📡 prod-frankfurt-02 (✅ Healthy)
│   │   │   └── 📡 prod-frankfurt-03 (⚠️  Warning)
│   │   └── 🔧 Environment: Staging
│   │       └── 📡 staging-frankfurt-01 (❌ Failed)
│   └── 🏭 Data Center: Amsterdam
│       └── 🔧 Environment: Production
│           └── 📡 prod-amsterdam-01 (✅ Healthy)
└── 📊 Group Health: 80% (4/5 healthy)
```

### **Przykład alertów i monitoringu dzienników:**
```
🚨 ALERT: nginx.service failed on staging-frankfurt-01
⏰ Time: 2024-01-15 14:32:15
📍 Server: staging-frankfurt-01
🔍 Service: nginx.service
📝 Error: Failed to start nginx.service: Unit nginx.service failed to load
📊 Severity: HIGH
🔄 Auto-retry: 3 attempts remaining
📧 Notification: Sent to admin@company.com
📱 Slack: #alerts-prod
```

### Integracja z Mancer:
- **Wykorzystanie SystemdService** z frameworka Mancer
- **Integracja z ProfileProducer** do zarządzania konfiguracją
- **Wykorzystanie istniejących backendów** SSH i lokalnych
- **Integracja z systemem logowania** Mancer
- **Wykorzystanie cache'owania** komend

### Funkcje sieciowe (Network-Oriented):
- **Zarządzanie wieloma serwerami jednocześnie** przez SSH
- **Konfiguracja grup serwerów** (produkcja, staging, development)
- **Load balancing** i failover dla operacji systemd
- **Monitorowanie połączeń sieciowych** (ping, connectivity)
- **Bezpieczne zarządzanie SSH** (klucze, hasła, known_hosts)
- **Firewall i security rules** dla dostępu SSH
- **Latency monitoring** i optymalizacja połączeń
- **Bulk operations** na wielu serwerach
- **Network topology** i routing dla zarządzania systemd

### **Enterprise Group Management:**
- **Hierarchiczne grupy serwerów** (Data Center → Region → Environment → Server)
- **Role-based access control** (RBAC) dla grup
- **Bulk operations na grupach** - operacje na wszystkich serwerach w grupie
- **Group templates** - szablony konfiguracji dla grup
- **Group health monitoring** - status zdrowia całej grupy
- **Group rollback** - cofanie zmian na poziomie grupy
- **Group synchronization** - synchronizacja konfiguracji między grupami

### **Log Monitoring & Alerting:**
- **Przeszukiwanie dzienników systemd** (journalctl) w czasie rzeczywistym
- **Wykrywanie błędów i ostrzeżeń** automatycznie
- **Inteligentne filtry dzienników** - edytowalne reguły i wzorce
- **Alerty w czasie rzeczywistym** - email, Slack, webhook, SMS
- **Escalation policies** - automatyczne eskalowanie alertów
- **Log aggregation** - zbieranie dzienników z wszystkich serwerów
- **Pattern recognition** - wykrywanie wzorców błędów
- **Performance monitoring** - monitorowanie wydajności usług
- **Custom alert rules** - konfigurowalne reguły alertów
- **Alert history** - historia alertów i akcji

### **Hybrydowe zarządzanie (Lokalne + Zdalne):**
- **Jednoczesne połączenie** do lokalnego systemu i zdalnych serwerów
- **Równoległe operacje** na lokalnym i zdalnych źródłach systemd
- **Osobne przedstawianie wyników** dla każdego źródła podczas wyszukiwania
- **Porównanie statusów** między lokalnym a zdalnymi systemami
- **Synchronizacja konfiguracji** między lokalnym a zdalnymi serwerami
- **Hybrydowe wyszukiwanie** - wyniki z lokalnego + wszystkich zdalnych źródeł
- **Kontrola dostępu** - różne uprawnienia dla lokalnego vs zdalnych
- **Cache'owanie** wyników z różnych źródeł osobno

## Architektura

- **Interfejs TUI**: Rich + ncurses
- **Backend**: Integracja z Mancer SystemdService
- **Komunikacja hybrydowa**: 
  - **Lokalne**: Bezpośrednie polecenia systemctl
  - **Zdalne**: SSH + polecenia systemctl
- **Zarządzanie wieloma źródłami**: 
  - Lokalny system + zdalne serwery
  - Równoległe operacje na wszystkich źródłach
  - Osobne cache'owanie i prezentacja wyników
- **Zarządzanie wieloma serwerami**: Konfiguracja grup serwerów, load balancing
- **Bezpieczeństwo sieciowe**: Szyfrowanie SSH, klucze publiczne, firewall rules
- **Monitorowanie sieci**: Ping, connectivity check, latency monitoring
- **Enterprise Group Management**: Hierarchiczne grupy, RBAC, templates
- **Log Monitoring & Alerting**: journalctl, pattern recognition, alerty
- **Konfiguracja**: YAML z autouzupełnianiem
- **Logi**: Integracja z journalctl i Mancer logger

## Wymagania

- Python 3.8+
- Rich (TUI framework)
- ncurses
- **SSH access do serwerów** (klucze publiczne lub hasła)
- **Dostęp sieciowy** do docelowych serwerów (port 22)
- **Framework Mancer** z obsługą SSH backend
- **systemd na docelowych systemach**
- **Stabilne połączenie sieciowe** dla zarządzania wieloma serwerami
