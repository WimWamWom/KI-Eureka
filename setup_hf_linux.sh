#!/bin/bash
# ============================================================
# HuggingFace Setup für Linux Server
# ============================================================

set -e

echo "======================================================================"
echo "  HuggingFace-Zugang einrichten"
echo "======================================================================"
echo ""

# Farben
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

# Virtuelle Umgebung aktivieren
if [ ! -d "venv" ]; then
    echo -e "${RED}✗ Virtuelle Umgebung nicht gefunden!${NC}"
    echo -e "${YELLOW}Führen Sie zuerst ./install_linux.sh aus${NC}"
    exit 1
fi

source venv/bin/activate

# Schritt 1: huggingface-cli prüfen
echo -e "${YELLOW}[1/4] Prüfe huggingface-cli...${NC}"
if command -v huggingface-cli &> /dev/null; then
    echo -e "${GREEN}  ✓ huggingface-cli ist installiert${NC}"
else
    echo -e "${YELLOW}  Installiere huggingface_hub...${NC}"
    pip install huggingface_hub
    echo -e "${GREEN}  ✓ huggingface_hub installiert${NC}"
fi

echo ""

# Schritt 2: Login-Status prüfen
echo -e "${YELLOW}[2/4] Prüfe Login-Status...${NC}"
if huggingface-cli whoami &> /dev/null; then
    USERNAME=$(huggingface-cli whoami 2>&1 | head -n1)
    echo -e "${GREEN}  ✓ Bereits angemeldet als: $USERNAME${NC}"
    read -p "  Neu anmelden? (j/N): " ANSWER
    if [[ ! "$ANSWER" =~ ^[jJ]$ ]]; then
        SKIP_LOGIN=true
    fi
else
    echo -e "${CYAN}  Noch nicht angemeldet${NC}"
fi

echo ""

# Schritt 3: Login
if [ "$SKIP_LOGIN" != true ]; then
    echo -e "${YELLOW}[3/4] HuggingFace-Login...${NC}"
    echo ""
    echo -e "${CYAN}Schritte:${NC}"
    echo "  1. Besuchen Sie: https://huggingface.co/settings/tokens"
    echo "  2. Klicken Sie 'New token'"
    echo "  3. Name: mistral (beliebig)"
    echo "  4. Type: Read"
    echo "  5. Kopieren Sie das Token"
    echo ""
    echo -e "${YELLOW}Fügen Sie Ihr Token ein:${NC}"

    huggingface-cli login

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}  ✓ Login erfolgreich!${NC}"
    else
        echo -e "${RED}  ✗ Login fehlgeschlagen${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}[3/4] Login übersprungen${NC}"
fi

echo ""

# Schritt 4: Modell-Zugang testen
echo -e "${YELLOW}[4/4] Teste Modell-Zugang...${NC}"
echo -e "${CYAN}  Dies kann einige Sekunden dauern...${NC}"

TEST_RESULT=$(python -c "
from transformers import AutoTokenizer
try:
    tokenizer = AutoTokenizer.from_pretrained('mistralai/Mistral-7B-Instruct-v0.3')
    print('SUCCESS')
except Exception as e:
    print(f'ERROR: {e}')
" 2>&1)

if echo "$TEST_RESULT" | grep -q "SUCCESS"; then
    echo -e "${GREEN}  ✓ Modell-Zugang erfolgreich!${NC}"
    echo -e "${GREEN}  ✓ Tokenizer wurde geladen${NC}"
elif echo "$TEST_RESULT" | grep -q "401"; then
    echo -e "${RED}  ✗ Zugriff verweigert (401 Unauthorized)${NC}"
    echo ""
    echo -e "${YELLOW}Bitte beantragen Sie Zugang zum Modell:${NC}"
    echo "  https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.3"
    echo ""
    echo "  1. Klicken Sie 'Access repository' (falls vorhanden)"
    echo "  2. Akzeptieren Sie die Nutzungsbedingungen"
    echo "  3. Zugang wird normalerweise sofort gewährt"
    echo ""
    echo -e "${CYAN}Nach der Genehmigung führen Sie dieses Skript erneut aus.${NC}"
elif echo "$TEST_RESULT" | grep -q "ERROR"; then
    echo -e "${YELLOW}  ⚠ Warnung: Konnte Modell nicht testen${NC}"
    echo -e "${RED}  Fehler: $TEST_RESULT${NC}"
else
    echo -e "${YELLOW}  ⚠ Unerwartete Ausgabe${NC}"
fi

echo ""
echo "======================================================================"
echo -e "${GREEN}Setup abgeschlossen!${NC}"
echo "======================================================================"
echo ""
echo -e "${CYAN}Nächste Schritte:${NC}"
echo ""
echo "  1. Virtuelle Umgebung aktivieren:"
echo "     source venv/bin/activate"
echo ""
echo "  2. Workflow starten:"
echo "     python main.py jsonl          # Trainingsdaten erstellen"
echo "     python main.py training       # Modell trainieren"
echo "     python main.py test           # Modell testen"
echo "     python main.py konvertiere    # Excel → XML"
echo ""
echo "Dokumentation: docs/MISTRAL_SETUP.md"
echo ""

