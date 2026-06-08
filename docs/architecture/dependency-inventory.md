# Inwentaryzacja zależności między warstwami (DDD)

Dokument mapuje importy między pakietami `domain`, `application`, `infrastructure` i `interface` oraz wskazuje naruszenia granic warstw.

## Zasada granic

- **domain**: tylko modele i abstrakcje (interfejsy/protokoły); brak zależności od `infrastructure`.
- **application**: orkiestracja; może zależeć od `domain` i `infrastructure`.
- **infrastructure**: implementacje; zależy od `domain` (interfejsy, modele).
- **interface**: entrypointy; zależy od `application`/`domain`.

## Mapa zależności (stan przed refaktorem)

### domain

- **domain.model** → domain.service (np. `command_result` → `data_converter_service`, `text_renderer`) — dozwolone.
- **domain.interface** → domain.model — dozwolone.
- **domain.service** → domain.model, domain.interface — dozwolone.
- **domain.shared.profile_producer** → **infrastructure.shared.ssh_connecticer** — **naruszenie**.
- **domain.shared.config_balancer** → **infrastructure.shared.file_tracer**, **infrastructure.shared.ssh_connecticer** — **naruszenie**.
- **domain.service.ssh_session_service** → **infrastructure.backend.ssh_backend** — **naruszenie** (orchestracja SSH powinna być w application).

### application

- **application.shell_runner** → domain.*, infrastructure.factory, infrastructure.backend, infrastructure.logging — dozwolone.
- **application.command_cache** → domain.model — dozwolone.
- **application.commands.base_command** → domain.*, infrastructure.backend — dozwolone (warstwa application może używać infrastructure); ta ścieżka jest oznaczona do zdeprecjonowania na rzecz infrastructure/command.
- **application.service.systemd_inspector** → domain.*, infrastructure.command, infrastructure.shared — dozwolone.
- **application.service.remote_config_manager** → domain.*, infrastructure.shared — dozwolone.

### infrastructure

- **infrastructure.*** → domain (interface, model) — dozwolone.
- **infrastructure.command.base_command** → domain.*, infrastructure.backend (BashBackend) — dozwolone.
- **infrastructure.shared.file_tracer** → infrastructure.backend, ssh_connecticer — dozwolone.

### interface

- Pliki `cli_interface.py`, `api_interface.py`, `command_builder.py` są placeholderami (krótki komentarz); entrypoint: ShellRunner.

## Wykaz naruszeń (domain → infrastructure)

| Plik w domain | Import z infrastructure | Uwagi |
|---------------|-------------------------|--------|
| `domain/shared/profile_producer.py` | `SSHConnecticer` | `ConnectionProfile.create_ssh_connection()` i `ProfileProducer.create_connection()` zwracają typ z infrastructure. |
| `domain/shared/config_balancer.py` | `FileTracer`, `SSHConnecticer` | `ConfigBalancer` tworzy/używa tych klas bezpośrednio. |
| `domain/service/ssh_session_service.py` | `SshBackendFactory`, `SSHSession`, `SCPTransfer`, `SSHSessionConfigDict` | Serwis jest faktycznie orkiestracją SSH — powinien być w application. |

## Duplikacja koncepcji Command

- **Kanoniczny model**: `src/mancer/infrastructure/command/base_command.py` (Pydantic, `_get_backend(context)`, mixiny).
- **Legacy**: `src/mancer/application/commands/base_command.py` (mutowalny builder, bezpośrednie importy backendów, niepełna obsługa SSH).
- **Rekomendacja**: Jeden model w infrastructure; komendy z application/commands migrowane lub wycofane do legacy.

## Po refaktorze (zrealizowane zmiany)

- **domain** nie importuje infrastructure. Usunięto importy: `SSHConnecticer`, `FileTracer` z profile_producer i config_balancer; `ssh_session_service` przeniesiony do application.
- **profile_producer**: `ConnectionProfile` nie tworzy już połączenia; `ProfileProducer.get_connection_profile(name)` zwraca profil; fabryka `create_ssh_from_profile(profile)` w `infrastructure.shared.ssh_connecticer` tworzy `SSHConnecticer`.
- **config_balancer**: Wprowadzono protokół `FileContentProvider` w `domain.interface.file_content_provider`; `ConfigBalancer.compare_configs` i `sync_config` przyjmują `source_provider` i `target_provider` (wstrzykiwane z application/infrastructure). Adapter `FileTracerContentProvider` w `infrastructure.shared.file_tracer_adapter`.
- **SSHSessionService** przeniesiony z `domain.service` do `application.service`; eksportowany z `mancer.application`.
- Jedna kanoniczna baza komend w infrastructure; application używa jej przez fabrykę (bez zmian w tym kroku).
