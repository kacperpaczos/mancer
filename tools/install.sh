#!/bin/bash

# Skrypt instalacyjny dla frameworka Mancer
set -e

echo "Rozpoczynam instalację frameworka Mancer..."

# Sprawdzanie czy Python jest zainstalowany
if ! command -v python3 &> /dev/null; then
    echo "Python 3 nie jest zainstalowany. Proszę zainstalować Python 3.8 lub nowszy."
    exit 1
fi

# Tworzenie wirtualnego środowiska
echo "Tworzenie wirtualnego środowiska..."
python3 -m venv .venv
source .venv/bin/activate

# Aktualizacja pip
echo "Aktualizacja pip..."
pip install --upgrade pip

# Instalacja zależności
echo "Instalacja zależności..."
pip install -r requirements.txt

# Deinstalacja wcześniejszej wersji Mancer (jeśli istnieje)
echo "Usuwanie poprzedniej instalacji Mancer (jeśli istnieje)..."
pip uninstall -y mancer || true

# Instalacja Mancer w trybie edycji
echo "Instalacja Mancer w trybie rozwojowym..."
pip install -e .

# Sprawdzenie instalacji
echo "Sprawdzanie instalacji..."
python -c "import mancer; print('Mancer zainstalowany pomyślnie!')"

echo "Instalacja zakończona pomyślnie."
echo "Możesz teraz używać frameworka Mancer."
echo "Aby aktywować środowisko wirtualne, użyj komendy: source .venv/bin/activate"
echo "Przykłady użycia znajdziesz w katalogu 'examples'." 