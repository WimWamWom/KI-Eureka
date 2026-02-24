#!/bin/bash
# ============================================================
# KI-Eureka Installation auf Linux Server
# ============================================================

set -e  # Bei Fehler abbrechen

echo "======================================================================"
echo "  KI-Eureka Installation auf Linux Server"
echo "======================================================================"
echo ""

# Farben für Ausgabe
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Schritt 1: Python-Version prüfen
echo -e "${YELLOW}[1/8] Prüfe Python-Version...${NC}"
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 10 ]; then
    echo -e "${GREEN}  ✓ Python $PYTHON_VERSION ist installiert${NC}"
else
    echo -e "${RED}  ✗ Python 3.10+ erforderlich, gefunden: $PYTHON_VERSION${NC}"
    echo -e "${YELLOW}  Installiere Python 3.11...${NC}"
    sudo apt update
    sudo apt install -y python3.11 python3.11-venv python3.11-dev
    # Verwende python3.11 statt python3
    PYTHON_CMD=python3.11
fi

# Verwende Standard-Python wenn nicht gesetzt
PYTHON_CMD=${PYTHON_CMD:-python3}

echo ""

# Schritt 2: Erforderliche System-Bibliotheken prüfen und installieren
echo -e "${YELLOW}[2/8] Prüfe System-Bibliotheken...${NC}"
MISSING_LIBS=()

# Prüfe ob liblzma installiert ist
if ! ldconfig -p | grep -q liblzma; then
    MISSING_LIBS+=("liblzma-dev")
fi

# Weitere wichtige Bibliotheken
if ! dpkg -l | grep -q "python3-dev"; then
    MISSING_LIBS+=("python3-dev")
fi

if ! dpkg -l | grep -q "build-essential"; then
    MISSING_LIBS+=("build-essential")
fi

if [ ${#MISSING_LIBS[@]} -gt 0 ]; then
    echo -e "${YELLOW}  Installiere fehlende Bibliotheken: ${MISSING_LIBS[*]}${NC}"
    sudo apt update
    sudo apt install -y "${MISSING_LIBS[@]}"
    echo -e "${GREEN}  ✓ Bibliotheken installiert${NC}"
else
    echo -e "${GREEN}  ✓ Alle System-Bibliotheken vorhanden${NC}"
fi

echo ""

# Schritt 3: CUDA prüfen (optional, aber wichtig für GPU)
echo -e "${YELLOW}[3/8] Prüfe CUDA/GPU...${NC}"
if command -v nvidia-smi &> /dev/null; then
    CUDA_VERSION=$(nvidia-smi | grep "CUDA Version" | awk '{print $9}')
    GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | head -n1)
    echo -e "${GREEN}  ✓ GPU gefunden: $GPU_NAME${NC}"
    echo -e "${GREEN}  ✓ CUDA Version: $CUDA_VERSION${NC}"
    HAS_GPU=true
else
    echo -e "${YELLOW}  ⚠ Keine NVIDIA GPU gefunden (Training auf CPU sehr langsam!)${NC}"
    HAS_GPU=false
fi

echo ""

# Schritt 4: Virtuelle Umgebung erstellen
echo -e "${YELLOW}[4/8] Erstelle virtuelle Umgebung...${NC}"
if [ -d "venv" ]; then
    echo -e "${YELLOW}  ⚠ venv existiert bereits, lösche und erstelle neu...${NC}"
    rm -rf venv
fi

$PYTHON_CMD -m venv venv
echo -e "${GREEN}  ✓ Virtuelle Umgebung erstellt${NC}"

echo ""

# Schritt 5: Virtuelle Umgebung aktivieren
echo -e "${YELLOW}[5/8] Aktiviere virtuelle Umgebung...${NC}"
source venv/bin/activate
echo -e "${GREEN}  ✓ Virtuelle Umgebung aktiviert${NC}"

echo ""

# Schritt 6: pip aktualisieren
echo -e "${YELLOW}[6/8] Aktualisiere pip, setuptools und wheel...${NC}"
pip install --upgrade pip setuptools wheel
echo -e "${GREEN}  ✓ pip aktualisiert${NC}"

echo ""

# Schritt 7: PyTorch installieren
echo -e "${YELLOW}[7/8] Installiere PyTorch...${NC}"
if [ "$HAS_GPU" = true ]; then
    # CUDA-Version bestimmen
    CUDA_MAJOR=$(echo $CUDA_VERSION | cut -d. -f1)
    CUDA_MINOR=$(echo $CUDA_VERSION | cut -d. -f2)

    if [ "$CUDA_MAJOR" -eq 12 ]; then
        echo -e "${CYAN}  Installiere PyTorch für CUDA 12.1...${NC}"
        pip install torch --index-url https://download.pytorch.org/whl/cu121
    elif [ "$CUDA_MAJOR" -eq 11 ]; then
        echo -e "${CYAN}  Installiere PyTorch für CUDA 11.8...${NC}"
        pip install torch --index-url https://download.pytorch.org/whl/cu118
    else
        echo -e "${YELLOW}  ⚠ Unbekannte CUDA-Version, installiere Standard-PyTorch...${NC}"
        pip install torch
    fi
else
    echo -e "${CYAN}  Installiere PyTorch (CPU-Version)...${NC}"
    pip install torch
fi
echo -e "${GREEN}  ✓ PyTorch installiert${NC}"

echo ""

# Schritt 8: requirements.txt installieren
echo -e "${YELLOW}[8/8] Installiere weitere Abhängigkeiten...${NC}"
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo -e "${GREEN}  ✓ Abhängigkeiten installiert${NC}"
else
    echo -e "${RED}  ✗ requirements.txt nicht gefunden!${NC}"
    exit 1
fi

echo ""

# Verifikation
echo "======================================================================"
echo -e "${GREEN}  Installation abgeschlossen!${NC}"
echo "======================================================================"
echo ""

# PyTorch testen
echo -e "${YELLOW}Teste PyTorch...${NC}"
python -c "import torch; print(f'  PyTorch Version: {torch.__version__}')"
python -c "import torch; print(f'  CUDA verfügbar: {torch.cuda.is_available()}')"
if [ "$HAS_GPU" = true ]; then
    python -c "import torch; print(f'  GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"keine\"}')"
fi

echo ""

# _lzma testen
echo -e "${YELLOW}Teste _lzma Modul...${NC}"
if python -c "import _lzma" 2>/dev/null; then
    echo -e "${GREEN}  ✓ _lzma ist verfügbar${NC}"
else
    echo -e "${RED}  ✗ _lzma nicht verfügbar${NC}"
    echo -e "${YELLOW}  Siehe docs/LZMA_FIX.md für Lösungen${NC}"
fi

echo ""

# Installationstest
echo -e "${YELLOW}Teste KI-Eureka Installation...${NC}"
python main.py --help > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}  ✓ KI-Eureka läuft korrekt${NC}"
else
    echo -e "${RED}  ✗ KI-Eureka konnte nicht gestartet werden${NC}"
fi

echo ""
echo "======================================================================"
echo -e "${CYAN}Nächste Schritte:${NC}"
echo "======================================================================"
echo ""
echo "1. HuggingFace-Zugang einrichten:"
echo "   ./setup_hf_linux.sh"
echo ""
echo "2. Trainingsdaten vorbereiten:"
echo "   # Excel-Dateien nach daten/trainingsdaten/eingabe_excel/ kopieren"
echo "   # XML-Dateien nach daten/trainingsdaten/eingabe_xml/ kopieren"
echo ""
echo "3. Workflow starten:"
echo "   source venv/bin/activate  # Virtuelle Umgebung aktivieren"
echo "   python main.py jsonl      # Trainingsdaten erstellen"
echo "   python main.py training   # Modell trainieren (1-3 Stunden)"
echo "   python main.py test       # Modell testen"
echo "   python main.py konvertiere daten/eingabe/datei.xlsx"
echo ""
echo "Dokumentation:"
echo "  - README.md"
echo "  - docs/MISTRAL_SETUP.md"
echo "  - docs/LZMA_FIX.md"
echo ""

