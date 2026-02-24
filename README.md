# KI-Eureka - Excel zu XML Konverter

Automatische Konvertierung von LAF-Excel-Formularen zu XML mit KI (Mistral-7B).

---

## 🎯 Was macht dieses Projekt?

Dieses Programm nutzt künstliche Intelligenz, um Excel-Dateien automatisch in XML-Format zu konvertieren.

**Workflow:**
1. Sie trainieren das KI-Modell einmalig mit Beispieldaten
2. Danach konvertiert die KI beliebig viele Excel-Dateien zu XML

---

## 📋 Was Sie brauchen

### Für Windows (lokale Entwicklung)
- Windows 10/11
- Python 3.10 oder neuer
- NVIDIA GPU mit min. 12 GB VRAM (empfohlen: 24 GB)
- 50 GB freier Speicherplatz
- Internet-Verbindung

### Für Linux Server (empfohlen für Training)
- Linux Server (Ubuntu 20.04+)
- SSH-Zugang zum Server
- NVIDIA GPU mit min. 12 GB VRAM
- 50 GB freier Speicherplatz

---

## 🚀 Installation

### Windows

**Schritt 1: Projekt herunterladen**
```powershell
# Laden Sie das Projekt herunter oder klonen Sie es
git clone https://github.com/<ihr-username>/KI-Eureka.git
cd KI-Eureka
```

**Schritt 2: Virtuelle Umgebung erstellen**
```powershell
# Erstellen
python -m venv venv

# Aktivieren
.\venv\Scripts\Activate.ps1
```

**Schritt 3: PyTorch installieren**
```powershell
# Für NVIDIA GPU mit CUDA 12.1
pip install torch --index-url https://download.pytorch.org/whl/cu121

# ODER für CUDA 11.8
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

**Schritt 4: Weitere Pakete installieren**
```powershell
pip install -r requirements.txt
```

**Schritt 5: HuggingFace-Login**
```powershell
huggingface-cli login
# Token eingeben von: https://huggingface.co/settings/tokens
```

---

### Linux Server

**Schritt 1: Projekt auf Server laden**
```bash
# Variante A: Git Clone
git clone https://github.com/<ihr-username>/KI-Eureka.git
cd KI-Eureka

# Variante B: Von Windows hochladen
# (In Windows PowerShell):
# scp -r C:\Users\wroehner\Desktop\Git\KI-Eureka user@server:~/
```

**Schritt 2: System-Pakete installieren**
```bash
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev build-essential liblzma-dev
```

**Schritt 3: Virtuelle Umgebung erstellen und aktivieren**
```bash
python3.11 -m venv venv
source venv/bin/activate
```

**Schritt 4: PyTorch installieren**
```bash
# Für NVIDIA GPU mit CUDA 12.1
pip install torch --index-url https://download.pytorch.org/whl/cu121

# ODER für CUDA 11.8
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

**Schritt 5: Weitere Pakete installieren**
```bash
pip install -r requirements.txt
```

**Schritt 6: HuggingFace-Login**
```bash
huggingface-cli login
# Token eingeben von: https://huggingface.co/settings/tokens
```

---

## 📚 Schritt-für-Schritt Anleitung

### 1️⃣ Trainingsdaten vorbereiten

Sie brauchen **Excel- und XML-Paare** zum Trainieren:

```
daten/trainingsdaten/eingabe_excel/
  ├── Formular1.xlsx
  ├── Formular2.xlsx
  └── Formular3.xlsx

daten/trainingsdaten/eingabe_xml/
  ├── Formular1.xml    ← Gleicher Name wie Excel!
  ├── Formular2.xml
  └── Formular3.xml
```

**Minimum:** 5 Paare  
**Empfohlen:** 20+ Paare für bessere Qualität

**Auf Linux-Server hochladen:**
```powershell
# Von Windows
scp C:\Pfad\zu\excel\*.xlsx user@server:~/KI-Eureka/daten/trainingsdaten/eingabe_excel/
scp C:\Pfad\zu\xml\*.xml user@server:~/KI-Eureka/daten/trainingsdaten/eingabe_xml/
```

---

### 2️⃣ JSONL-Trainingsdaten erstellen

**Windows:**
```powershell
python main.py jsonl
```

**Linux:**
```bash
source venv/bin/activate
python main.py jsonl
```

**Was passiert:**
- Excel-Dateien werden in JSON umgewandelt
- JSON und XML werden zu Trainingspaaren kombiniert
- Ergebnis: `daten/trainingsdaten/jsonl/training_data_json.jsonl`

**Dauer:** 1-5 Minuten

---

### 3️⃣ KI-Modell trainieren

**⚠️ WICHTIG: Training dauert 1-3 Stunden!**

**Linux oder Windows:**
```bash
python main.py training
```

**Optional (mehr Qualität):**
```bash
python main.py training --epochs 5
```

**Was passiert:**
- Das Mistral-7B Modell wird heruntergeladen (~14 GB, nur beim ersten Mal)
- Das Modell lernt von Ihren Trainingspaaren
- Ergebnis: Trainiertes Modell in `modell/modell_output/`

**Dauer:** 
- Erster Start: 30-90 Min (Modell-Download + Training)
- Nachfolgende Trainings: 30-120 Min (nur Training)

**Fortschritt überwachen:**
```bash
# In separatem Terminal:
watch -n 2 nvidia-smi    # GPU-Auslastung
tail -f pipeline.log     # Training-Log
```

---

### 4️⃣ Modell testen (optional)

```bash
python main.py test
```

**Was passiert:**
- Testet das Modell mit Excel-Dateien aus `daten/testdaten/test_excel/`
- Zeigt Qualitätsbericht an
- Ergebnis: Test-XMLs in `daten/ausgabe/testergebnisse/`

**Dauer:** 5-15 Minuten

---

### 5️⃣ Excel zu XML konvertieren

**Jetzt können Sie beliebige Excel-Dateien konvertieren!**

**Einzelne Datei:**
```bash
python main.py konvertiere daten/eingabe/MeinFormular.xlsx
```

**Mehrere Dateien:**
```bash
python main.py konvertiere daten/eingabe/Datei1.xlsx daten/eingabe/Datei2.xlsx
```

**Ganzer Ordner:**
```bash
python main.py konvertiere daten/eingabe/
```

**Ergebnis:** XML-Dateien in `daten/ausgabe/`

**Dauer:** 10-30 Sekunden pro Datei

---

## 🔄 Tägliche Nutzung

Nach dem einmaligen Training:

```bash
# 1. Virtuelle Umgebung aktivieren
source venv/bin/activate          # Linux
.\venv\Scripts\Activate.ps1       # Windows

# 2. Excel-Datei konvertieren
python main.py konvertiere daten/eingabe/ihre-datei.xlsx

# 3. Fertig! XML liegt in daten/ausgabe/
```

---

## 📁 Ordnerstruktur

```
KI-Eureka/
├── daten/
│   ├── trainingsdaten/
│   │   ├── eingabe_excel/       ← Excel-Dateien zum Trainieren hier rein
│   │   └── eingabe_xml/         ← Zugehörige XML-Dateien hier rein
│   ├── testdaten/
│   │   └── test_excel/          ← Test-Excel-Dateien (optional)
│   ├── eingabe/                 ← Excel-Dateien zum Konvertieren hier rein
│   └── ausgabe/                 ← Generierte XML-Dateien kommen hier raus
├── modell/
│   └── modell_output/           ← Trainiertes Modell (nach Training)
└── config.yaml                  ← Einstellungen
```

---

## ⚙️ Wichtige Einstellungen (config.yaml)

Öffnen Sie `config.yaml` zum Anpassen:

```yaml
# Modell
basis_modell: "mistralai/Mistral-7B-Instruct-v0.3"

# Training
num_train_epochs: 3              # Mehr = besser, aber länger
batch_size: 4                    # Bei Speicherfehler auf 2 reduzieren

# Generierung
temperature: 0.3                 # Niedriger = konsistenter
max_new_tokens: 4096            # Max. XML-Länge
retries: 3                       # Wiederholungen bei Fehlern
```

---

## ❓ Häufige Probleme

### "CUDA out of memory"
**Lösung:** In `config.yaml` ändern:
```yaml
batch_size: 2     # statt 4
```

### "ModuleNotFoundError: No module named '...'"
**Lösung:** Virtuelle Umgebung aktivieren:
```bash
source venv/bin/activate          # Linux
.\venv\Scripts\Activate.ps1       # Windows
```

### "401 Unauthorized" (HuggingFace)
**Lösung:** Neu anmelden:
```bash
huggingface-cli login
```
Token erstellen: https://huggingface.co/settings/tokens

### Training bricht ab / SSH-Verbindung verloren
**Lösung:** Screen verwenden (siehe Schritt 3)

### XML-Qualität schlecht
**Lösungen:**
1. Mehr Trainingsdaten (min. 20 Paare)
2. Mehr Epochs: `python main.py training --epochs 5`
3. Niedrigere temperature in `config.yaml`: `0.1`

### "ModuleNotFoundError: No module named '_lzma'" (nur Linux)
**Lösung:** Siehe Abschnitt "Erweiterte Themen → Linux: _lzma Fehler beheben" unten

---

## ✅ Checkliste: Bin ich bereit?

**Vor dem Training:**
- [ ] Python 3.10+ installiert
- [ ] Virtuelle Umgebung erstellt und aktiviert
- [ ] PyTorch mit CUDA installiert
- [ ] `pip install -r requirements.txt` ausgeführt
- [ ] HuggingFace-Login durchgeführt
- [ ] Min. 5 Excel+XML Paare in `daten/trainingsdaten/`
- [ ] 50 GB freier Speicherplatz

**Training starten:**
```bash
python main.py jsonl
python main.py training
```

**Nach dem Training:**
```bash
python main.py konvertiere daten/eingabe/ihre-datei.xlsx
```

---

## 🎯 Zusammenfassung in 5 Schritten

1. **Installation:** Python + venv + Abhängigkeiten installieren
2. **Trainingsdaten:** Excel + XML in `daten/trainingsdaten/` kopieren
3. **Training:** `python main.py jsonl` → `python main.py training`
4. **Testen:** `python main.py test` (optional)
5. **Nutzen:** `python main.py konvertiere ihre-datei.xlsx`

**Fertig!** 🎉

---

## 💡 Tipps

- **Training auf Server:** Viel schneller mit dedizierter GPU
- **Screen verwenden:** Training läuft auch nach SSH-Disconnect weiter
- **Mehr Daten = bessere Qualität:** Mindestens 20 Trainingspaare sammeln
- **Regelmäßig testen:** Nach jedem Training `python main.py test` ausführen
- **Backups:** Trainiertes Modell aus `modell/modell_output/` sichern

---

## 🔧 Erweiterte Themen

### Linux: _lzma Fehler beheben

Falls auf Linux der Fehler `ModuleNotFoundError: No module named '_lzma'` auftritt:

**Lösung 1: System-Bibliothek installieren**
```bash
# Ubuntu/Debian
sudo apt install liblzma-dev

# Red Hat/CentOS
sudo yum install xz-devel

# Dann Python neu kompilieren oder venv neu erstellen
```

**Lösung 2: Distribution-Python verwenden**
```bash
sudo apt install python3.11 python3.11-venv
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Die Modi `konvertiere` und `--help` funktionieren auch ohne _lzma. Nur `jsonl`, `training` und `test` benötigen es.

---

### Alternative Mistral-Modelle

Falls Sie ein anderes Modell verwenden möchten, ändern Sie in `config.yaml`:

```yaml
# Mistral 7B v0.2 (keine Zugangsgenehmigung nötig)
basis_modell: "mistralai/Mistral-7B-Instruct-v0.2"

# Mistral 7B v0.1 (älteste Version)
basis_modell: "mistralai/Mistral-7B-Instruct-v0.1"
```

Nach Modellwechsel sollten Sie das Training neu durchführen.

---

### HuggingFace-Token einrichten

**Schritt 1:** Konto erstellen bei https://huggingface.co/join

**Schritt 2:** Token erstellen bei https://huggingface.co/settings/tokens
- Name: `mistral` (beliebig)
- Type: **Read**
- Token kopieren

**Schritt 3:** Modell-Zugang beantragen
- Besuchen Sie: https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.3
- Falls Button "Access repository" erscheint: Klicken und Bedingungen akzeptieren
- Zugang wird sofort gewährt

**Schritt 4:** Login durchführen
```bash
huggingface-cli login
# Token einfügen
```

---

### Modell-Download

Beim ersten Training oder Konvertierung wird das Mistral-7B Modell automatisch heruntergeladen:
- **Größe:** ~14 GB
- **Dauer:** 10-60 Minuten (abhängig von Internet)
- **Speicherort:** `~/.cache/huggingface/` (Linux) oder `C:\Users\<user>\.cache\huggingface\` (Windows)
- **Nur einmalig:** Danach wird das gecachte Modell verwendet

---

### GPU-Anforderungen

**Minimum (Training möglich, aber langsam):**
- NVIDIA GPU mit 12 GB VRAM
- Batch-Size auf 1-2 reduzieren

**Empfohlen (optimale Performance):**
- NVIDIA GPU mit 24 GB VRAM (z.B. RTX 3090, RTX 4090, A5000)
- Batch-Size 4

**CPU-Only (nicht empfohlen):**
- Training dauert 50-100x länger
- Nur für Tests sinnvoll

---

### Projektstruktur im Detail

```
KI-Eureka/
├── main.py                      # Hauptprogramm (alle Modi)
├── config.yaml                  # Konfiguration
├── requirements.txt             # Python-Abhängigkeiten
├── core/                        # Programm-Module
│   ├── config.py                # Konfiguration laden
│   ├── excel_parser.py          # Excel einlesen
│   ├── jsonl_ersteller.py       # JSONL-Trainingsdaten erstellen
│   ├── trainer.py               # KI-Training (QLoRA)
│   ├── ki_generator.py          # XML generieren
│   ├── tester.py                # Modell testen
│   ├── xml_validator.py         # XML-Validierung
│   └── file_writer.py           # XML speichern
├── daten/
│   ├── trainingsdaten/          # Daten fürs Training
│   │   ├── eingabe_excel/       # Excel-Trainingsdaten
│   │   ├── eingabe_xml/         # XML-Referenzen
│   │   ├── erzeugte_json/       # Auto-generiert
│   │   └── jsonl/               # Auto-generiert
│   ├── testdaten/               # Daten zum Testen
│   │   ├── test_excel/          # Test-Excel-Dateien
│   │   └── test_xml/            # XML-Referenzen
│   ├── eingabe/                 # Excel zum Konvertieren
│   ├── ausgabe/                 # Generierte XMLs
│   └── schema/                  # XSD-Schema (optional)
└── modell/
    ├── modell_output/           # Trainierter LoRA-Adapter
    ├── checkpoints/             # Training-Checkpoints
    └── logs/                    # Training-Logs
```

---

## 📞 Kontakt & Support

**Bei technischen Problemen:**
1. Prüfen Sie die Checkliste oben
2. Schauen Sie in die Sektion "Häufige Probleme"
3. Überprüfen Sie `pipeline.log` für detaillierte Fehlermeldungen

**Training-Logs:**
- Haupt-Log: `pipeline.log` (im Projektverzeichnis)
- Training-Details: `modell/logs/`

---

## 📄 Lizenz & Credits

- **Basis-Modell:** Mistral-7B-Instruct-v0.3 (Apache 2.0)
- **Projekt:** Entwickelt für LAF-Formularkonvertierung
- **Technologien:** Python, PyTorch, Transformers, PEFT, TRL

---

**Version:** 2.0  
**Zuletzt aktualisiert:** Februar 2026

