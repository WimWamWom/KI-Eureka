# Mistral-7B-Instruct-v0.3 Setup-Skript
# Führen Sie dieses Skript aus, um den HuggingFace-Zugang einzurichten

Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "  Mistral-7B-Instruct-v0.3 Setup" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host ""

# Schritt 1: Überprüfen ob huggingface-cli verfügbar ist
Write-Host "[1/4] Überprüfe huggingface-cli..." -ForegroundColor Yellow
try {
    $null = huggingface-cli --version
    Write-Host "  ✓ huggingface-cli ist installiert" -ForegroundColor Green
} catch {
    Write-Host "  ✗ huggingface-cli nicht gefunden" -ForegroundColor Red
    Write-Host "  Installiere huggingface_hub..." -ForegroundColor Yellow
    pip install huggingface_hub
}

Write-Host ""

# Schritt 2: Überprüfen ob bereits angemeldet
Write-Host "[2/4] Überprüfe HuggingFace-Login..." -ForegroundColor Yellow
try {
    $whoami = huggingface-cli whoami 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Bereits angemeldet als: $whoami" -ForegroundColor Green
        $neuLogin = Read-Host "  Möchten Sie sich neu anmelden? (j/N)"
        if ($neuLogin -ne "j" -and $neuLogin -ne "J") {
            Write-Host "  Behalte bestehenden Login" -ForegroundColor Cyan
            $skipLogin = $true
        }
    }
} catch {
    Write-Host "  Noch nicht angemeldet" -ForegroundColor Cyan
}

Write-Host ""

# Schritt 3: Login (falls erforderlich)
if (-not $skipLogin) {
    Write-Host "[3/4] HuggingFace-Login..." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Bitte besuchen Sie: https://huggingface.co/settings/tokens" -ForegroundColor Cyan
    Write-Host "  1. Erstellen Sie ein neues Token (Type: Read)" -ForegroundColor White
    Write-Host "  2. Kopieren Sie das Token" -ForegroundColor White
    Write-Host "  3. Fügen Sie es hier ein:" -ForegroundColor White
    Write-Host ""

    huggingface-cli login

    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Login erfolgreich!" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Login fehlgeschlagen" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "[3/4] Login übersprungen" -ForegroundColor Yellow
}

Write-Host ""

# Schritt 4: Modell-Zugang testen
Write-Host "[4/4] Teste Modell-Zugang..." -ForegroundColor Yellow
Write-Host "  Dies kann einige Sekunden dauern..." -ForegroundColor Cyan

$testScript = @"
from transformers import AutoTokenizer
try:
    tokenizer = AutoTokenizer.from_pretrained('mistralai/Mistral-7B-Instruct-v0.3')
    print('SUCCESS')
except Exception as e:
    print(f'ERROR: {e}')
"@

$result = python -c $testScript 2>&1

if ($result -match "SUCCESS") {
    Write-Host "  ✓ Modell-Zugang erfolgreich getestet!" -ForegroundColor Green
    Write-Host "  ✓ Tokenizer wurde geladen" -ForegroundColor Green
} elseif ($result -match "401") {
    Write-Host "  ✗ Zugriff verweigert (401 Unauthorized)" -ForegroundColor Red
    Write-Host ""
    Write-Host "  Bitte beantragen Sie Zugang zum Modell:" -ForegroundColor Yellow
    Write-Host "  https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.3" -ForegroundColor Cyan
    Write-Host "  Klicken Sie auf 'Access repository' und akzeptieren Sie die Bedingungen" -ForegroundColor White
} else {
    Write-Host "  ⚠ Warnung: Konnte Modell nicht testen" -ForegroundColor Yellow
    Write-Host "  Fehler: $result" -ForegroundColor Red
}

Write-Host ""
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "  Setup abgeschlossen!" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host ""
Write-Host "Nächste Schritte:" -ForegroundColor Yellow
Write-Host "  1. python main.py jsonl          # Trainingsdaten erstellen" -ForegroundColor White
Write-Host "  2. python main.py training       # Modell trainieren (1-3 Stunden)" -ForegroundColor White
Write-Host "  3. python main.py test           # Modell testen" -ForegroundColor White
Write-Host "  4. python main.py konvertiere    # Excel → XML konvertieren" -ForegroundColor White
Write-Host ""
Write-Host "Weitere Informationen: docs\MISTRAL_SETUP.md" -ForegroundColor Cyan
Write-Host ""

