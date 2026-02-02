# Legacy commands (application/commands)

**Status: legacy / deprecated.** Nie używaj tych klas w nowym kodzie.

Kanoniczny model komend znajduje się w **`mancer.infrastructure.command`**:

- Bazowa klasa: `mancer.infrastructure.command.base_command.BaseCommand`
- Fabryka: `mancer.infrastructure.factory.command_factory.CommandFactory`
- ShellRunner używa wyłącznie komend z infrastructure przez CommandFactory.

Moduły w tym katalogu (`base_command`, `apt_command`, `systemctl_command`) to starsza warstwa z mutowalnym builderem i bezpośrednimi importami backendów; nie są rejestrowane w CommandFactory i nie są eksponowane w publicznym API. Zachowane dla kompatybilności wstecznej; w przyszłości mogą zostać usunięte lub przeniesione do infrastructure jako konkretne implementacje.
