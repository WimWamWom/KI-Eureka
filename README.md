# Excel → XML Pipeline mit KI-Unterstützung

KI-gestützte Anwendung, die LAF-Formular-Excel-Dateien mittels eines **fine-getunten Mistral-7B-Instruct-Modells** automatisiert in gültige **SpreadsheetML-XML-Dokumente** konvertiert. Das Modell wird lokal auf einer NVIDIA-GPU betrieben und durch Supervised Fine-Tuning (SFT) mit QLoRA auf die spezifische LAF-Formularstruktur spezialisiert.

---

## Inhaltsverzeichnis

1. [Funktionsübersicht](#1-funktionsübersicht)
2. [Systemanforderungen](#2-systemanforderungen)
3. [Projektstruktur](#3-projektstruktur)
4. [Installation](#4-installation)
5. [Workflow](#5-workflow-schritt-für-schritt)
   - [Schritt 1 – JSONL erzeugen](#schritt-1--jsonl-erzeugen)
   - [Schritt 2 – Modell trainieren](#schritt-2--modell-trainieren)
   - [Schritt 3 – Modell testen](#schritt-3--modell-testen)
   - [Schritt 4 – Excel konvertieren](#schritt-4--excel-konvertieren-finale-nutzung)
6. [Alle CLI-Optionen](#6-alle-cli-optionen)
7. [Konfiguration](#7-konfiguration-configyaml)
8. [Datenstruktur & Eingabeformat](#8-datenstruktur--eingabeformat)
9. [Fehlerbehandlung & Retry-Logik](#9-fehlerbehandlung--retry-logik)
10. [XSD-Schema-Validierung](#10-xsd-schema-validierung)
11. [Testmodus im Detail](#11-testmodus-im-detail)
12. [Architektur & Module](#12-architektur--module)
13. [Häufige Fehler & Lösungen](#13-häufige-fehler--lösungen)

---

## 1. Funktionsübersicht

| Funktion | Befehl | Beschreibung |
|---|---|---|
| JSONL erzeugen | `python main.py jsonl` | Trainingspaare aus JSON + XML generieren |
| Training | `python main.py training` | Mistral-7B per QLoRA fine-tunen |
| Test | `python main.py test` | KI-Qualität anhand vorhandener Daten prüfen |
| Konvertierung | `python main.py konvertiere <datei.xlsx>` | Excel-Datei → XML-Dokument |

---

## 2. Systemanforderungen

### Hardware

| Komponente | Minimum | Empfohlen |
|---|---|---|
| GPU VRAM | 12 GB | 15–24 GB |
| RAM | 16 GB | 32 GB |
| Speicherplatz | 30 GB | 50 GB |

> Das Modell wird in **4-bit QLoRA** geladen, was den VRAM-Bedarf stark reduziert. Eine NVIDIA GPU mit 15 GB VRAM ist ausreichend.

### Software

- **Python** 3.10 oder höher
- **CUDA** 11.8 oder 12.1
- **Windows** 10/11 (getestet)
- **Git** (optional, für Versionskontrolle)

---

## 3. Projektstruktur

```
excel_zu_xml/
│
├── main.py                          ← Einziger Einstiegspunkt (alle 4 Modi)
├── config.yaml                      ← Zentrale Konfigurationsdatei
├── requirements.txt                 ← Python-Abhängigkeiten
├── .gitignore
│
├── core/                            ← Modulare Programmlogik
│   ├── __init__.py                  – Paket-Exporte
│   ├── config.py                    – config.yaml laden → AppConfig
│   ├── models.py                    – Datenklassen (ExcelData, ConversionResult)
│   ├── excel_parser.py              – Excel einlesen → ExcelData
│   ├── jsonl_ersteller.py           – Excel → JSON → JSONL-Trainingsdaten
│   ├── trainer.py                   – QLoRA Fine-Tuning (SFT)
│   ├── ki_generator.py              – Modell laden + XML generieren (mit Retry)
│   ├── xml_validator.py             – Syntax- & XSD-Validierung, Pretty-Print
│   ├── tester.py                    – Automatisierter Testmodus
│   ├── file_writer.py               – XML-Datei speichern
│   └── logger.py                    – Zentrales Logging
│
├── daten/
│   ├── trainingsdaten/              ← Wird für das Training verwendet
│   │   ├── eingabe_excel/           ← Excel-Dateien als Trainingsinput
│   │   ├── erzeugte_json/           ← JSON automatisch aus Excel erzeugt
│   │   ├── eingabe_xml/             ← Referenz-XML (Soll-Ausgabe)
│   │   └── jsonl/                   ← Erzeugte JSONL-Datei
│   ├── testdaten/                   ← Wird für den Testmodus verwendet
│   │   ├── test_excel/              ← Excel-Dateien für den Test
│   │   ├── erzeugte_json/           ← JSON automatisch aus Excel erzeugt
│   │   └── test_xml/                ← Referenz-XML für Vergleich
│   ├── eingabe/                     ← Excel-Dateien für finale Nutzung ablegen
│   ├── ausgabe/                     ← Generierte XML-Ausgaben der KI
│   └── schema/                      ← XSD-Schema ablegen (optional, auto. erkannt)
│
├── modell/
│   ├── modell_output/               ← Trainierter LoRA-Adapter (nach Training)
│   ├── checkpoints/                 ← Zwischen-Checkpoints während des Trainings
│   └── logs/                        ← Trainings-Logs
│
└── docs/
    └── ARCHITEKTUR.md               ← Technische Architekturdokumentation
```

---

## 4. Installation

Die Installation gliedert sich in vier Schritte: Repository klonen, virtuelle Umgebung erstellen, PyTorch installieren und weitere Abhängigkeiten einrichten. Die Anleitung gilt sowohl für **Linux-Server** (empfohlen für Training) als auch für **Windows** (lokale Entwicklung).

---

### 🐧 Linux (empfohlen für Training auf Server)

#### Schritt 1 – Voraussetzungen prüfen

```bash
# Python-Version prüfen (muss 3.10+ sein)
python3 --version

# Git prüfen
git --version

# CUDA-Version prüfen (für PyTorch-Installation relevant)
nvidia-smi
```

Falls Python 3.10+ nicht installiert ist:

```bash
sudo apt update && sudo apt install -y python3.11 python3.11-venv python3-pip
```

#### Schritt 2 – Repository klonen

```bash
# Repository klonen (HTTPS)
git clone https://github.com/<dein-benutzername>/<dein-repo-name>.git

# In den Projektordner wechseln
cd <dein-repo-name>
```

> **Hinweis:** `<dein-benutzername>` und `<dein-repo-name>` durch deine tatsächlichen GitHub-Daten ersetzen.

#### Schritt 3 – Virtuelle Umgebung erstellen und aktivieren

```bash
# Virtuelle Umgebung erstellen
python3 -m venv venv

# Virtuelle Umgebung aktivieren
source venv/bin/activate

# Prüfen ob aktiviert (Prompt zeigt jetzt "(venv)")
which python
```

> **Wichtig:** Die virtuelle Umgebung muss **jedes Mal** nach einem neuen Terminal-Login erneut aktiviert werden:
> ```bash
> source venv/bin/activate
> ```

#### Schritt 4 – PyTorch mit CUDA installieren

PyTorch muss **vor** den anderen Paketen installiert werden. Die Version muss zur CUDA-Version des Servers passen:

```bash
# CUDA-Version aus nvidia-smi ablesen (z.B. "CUDA Version: 12.1")

# Für CUDA 12.1 (empfohlen):
pip install torch --index-url https://download.pytorch.org/whl/cu121

# Für CUDA 11.8:
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

CUDA-Verfügbarkeit prüfen:

```bash
python -c "import torch; print('CUDA verfügbar:', torch.cuda.is_available()); print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'keine')"
```

Erwartete Ausgabe:
```
CUDA verfügbar: True
GPU: NVIDIA GeForce RTX ...
```

#### Schritt 5 – Weitere Abhängigkeiten installieren

```bash
pip install -r requirements.txt
```

#### Schritt 6 – Installation prüfen

```bash
python main.py --help
```

---

### 🪟 Windows (lokale Entwicklung / Test)

#### Schritt 1 – Voraussetzungen prüfen

Folgende Programme müssen installiert sein:

| Programm | Download | Prüfen |
|---|---|---|
| Python 3.10+ | [python.org](https://www.python.org/downloads/) | `python --version` |
| Git | [git-scm.com](https://git-scm.com/) | `git --version` |
| NVIDIA-Treiber + CUDA | [developer.nvidia.com](https://developer.nvidia.com/cuda-downloads) | `nvidia-smi` |

> **Hinweis PowerShell-Ausführungsrichtlinie:** Falls Skripte blockiert werden, einmalig ausführen:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

#### Schritt 2 – Repository klonen

```powershell
# In den gewünschten Zielordner wechseln
cd "C:\Users\<benutzername>\Desktop"

# Repository klonen
git clone https://github.com/<dein-benutzername>/<dein-repo-name>.git

# In den Projektordner wechseln
cd <dein-repo-name>
```

#### Schritt 3 – Virtuelle Umgebung erstellen und aktivieren

```powershell
# Virtuelle Umgebung erstellen
python -m venv venv

# Virtuelle Umgebung aktivieren
.\venv\Scripts\Activate.ps1

# Prüfen ob aktiviert (Prompt zeigt jetzt "(venv)")
python --version
```

> **Wichtig:** Die virtuelle Umgebung muss **jedes Mal** nach einem neuen PowerShell-Fenster erneut aktiviert werden:
> ```powershell
> .\venv\Scripts\Activate.ps1
> ```

#### Schritt 4 – PyTorch mit CUDA installieren

```powershell
# CUDA-Version aus nvidia-smi ablesen

# Für CUDA 12.1 (empfohlen):
pip install torch --index-url https://download.pytorch.org/whl/cu121

# Für CUDA 11.8:
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

CUDA-Verfügbarkeit prüfen:

```powershell
python -c "import torch; print('CUDA:', torch.cuda.is_available()); print('GPU:', torch.cuda.get_device_name(0))"
```

#### Schritt 5 – Weitere Abhängigkeiten installieren

```powershell
pip install -r requirements.txt
```

#### Schritt 6 – Installation prüfen

```powershell
python main.py --help
```

---

### 📁 Ordner für Daten anlegen (einmalig)

Nach dem Klonen fehlen die leeren Datenordner (sie sind nicht in Git enthalten, da `.gitignore` sie ausschließt). Diese einmalig anlegen:

**Linux:**
```bash
mkdir -p daten/trainingsdaten/eingabe_excel \
         daten/trainingsdaten/erzeugte_json \
         daten/trainingsdaten/eingabe_xml \
         daten/trainingsdaten/jsonl \
         daten/testdaten/test_excel \
         daten/testdaten/erzeugte_json \
         daten/testdaten/test_xml \
         daten/eingabe \
         daten/ausgabe \
         daten/schema \
         modell/modell_output \
         modell/checkpoints \
         modell/logs
```

**Windows (PowerShell):**
```powershell
@(
  "daten\trainingsdaten\eingabe_excel",
  "daten\trainingsdaten\erzeugte_json",
  "daten\trainingsdaten\eingabe_xml",
  "daten\trainingsdaten\jsonl",
  "daten\testdaten\test_excel",
  "daten\testdaten\erzeugte_json",
  "daten\testdaten\test_xml",
  "daten\eingabe",
  "daten\ausgabe",
  "daten\schema",
  "modell\modell_output",
  "modell\checkpoints",
  "modell\logs"
) | ForEach-Object { New-Item -ItemType Directory -Force -Path $_ }
```

---

### 🔑 HuggingFace-Zugang einrichten (einmalig)

Das Basis-Modell `mistralai/Mistral-7B-Instruct-v0.3` wird automatisch von HuggingFace heruntergeladen (~14 GB). Dafür ist ein kostenloses HuggingFace-Konto und ein Access-Token erforderlich:

1. Konto erstellen: [huggingface.co](https://huggingface.co/join)
2. Token erstellen: [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) (Typ: `Read`)
3. Modell-Zugang beantragen: [huggingface.co/mistralai/Mistral-7B-Instruct-v0.3](https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.3) → „Access repository"
4. Token lokal speichern:

```bash
# Linux
pip install huggingface_hub
huggingface-cli login
# Token eingeben wenn gefragt
```

```powershell
# Windows
pip install huggingface_hub
huggingface-cli login
# Token eingeben wenn gefragt
```

> Das Modell wird beim ersten `python main.py training` oder `python main.py konvertiere` **automatisch heruntergeladen** und unter `~/.cache/huggingface/` gespeichert. Der Download dauert je nach Verbindung **10–60 Minuten** und geschieht nur einmalig.

---

## 5. Workflow (Schritt für Schritt)

Der vollständige Ablauf vom Rohdaten bis zum generierten XML gliedert sich in vier Schritte:

```
[JSON + XML]  →  [JSONL]  →  [Training]  →  [Test]  →  [Konvertierung]
   Schritt 1      Schritt 1    Schritt 2     Schritt 3     Schritt 4
```

---

### Schritt 1 – JSONL erzeugen

Aus den Excel-Dateien in `daten/trainingsdaten/eingabe_excel/` werden zunächst JSON-Dateien erzeugt (in `daten/trainingsdaten/erzeugte_json/`). Diese werden anschließend mit den Referenz-XMLs aus `daten/trainingsdaten/eingabe_xml/` zu JSONL-Trainingspaaren kombiniert. Jede Zeile enthält:

```json
{"id": "LAF__VN_Schlussbescheid", "prompt": "{...JSON aus Excel...}", "completion": "<Workbook>...</Workbook>"}
```

```powershell
python main.py jsonl
```

**Ausgabe:**
- `daten/trainingsdaten/erzeugte_json/` – JSON-Dateien aus Excel
- `daten/trainingsdaten/jsonl/training_data_json.jsonl` – JSONL für das Training

---

### Schritt 2 – Modell trainieren

Das Mistral-7B-Instruct-v0.3-Modell wird mittels **Supervised Fine-Tuning (SFT)** mit **QLoRA** (4-bit Quantisierung + LoRA-Adapter) auf die erzeugten Trainingsdaten spezialisiert. Das Basis-Modell wird dabei nicht verändert – nur ein leichtgewichtiger **LoRA-Adapter** (wenige MB) wird trainiert und gespeichert.

```powershell
python main.py training
```

Mit abweichender Epoch-Anzahl:

```powershell
python main.py training --epochs 5
```

> **Was ist eine Epoch?** Eine Epoch ist ein vollständiger Durchlauf durch den gesamten Trainingsdatensatz. Mit `--epochs 5` sieht das Modell alle Trainingsbeispiele fünfmal. Mehr Epochs bedeuten mehr Lernzeit, können aber bei zu kleinem Datensatz zu Overfitting führen (das Modell lernt die Trainingsdaten auswendig statt zu verallgemeinern). Der Standardwert `3` in `config.yaml` kann jederzeit ohne Code-Änderung mit `--epochs N` überschrieben werden.

**Ausgabe:** `modell/modell_output/` (LoRA-Adapter + Tokenizer)

**Trainingsparameter** (konfigurierbar in `config.yaml`):

| Parameter | Standard | Beschreibung |
|---|---|---|
| `num_train_epochs` | `3` | Trainings-Durchläufe über den gesamten Datensatz |
| `batch_size` | `4` | Beispiele pro GPU-Schritt |
| `learning_rate` | `0.0002` | Lernrate |
| `lora_r` | `16` | LoRA Rang (höher = mehr Parameter) |
| `lora_alpha` | `32` | LoRA Skalierungsfaktor |
| `max_seq_length` | `2048` | Maximale Sequenzlänge in Token |

> **Hinweis:** Das Training dauert je nach GPU und Datenmenge ca. 1–3 Stunden. Zwischen-Checkpoints werden in `modell/checkpoints/` gespeichert, sodass bei Unterbrechung nicht von vorne begonnen werden muss.

---

### Schritt 3 – Modell testen

Der Testmodus prüft die Qualität des trainierten Modells vollautomatisch anhand der Excel-Dateien in `daten/testdaten/test_excel/`. Für jede Datei wird:

1. Die Excel eingelesen und JSON in `daten/testdaten/erzeugte_json/` gespeichert
2. Das Modell generiert ein XML (mit bis zu 3 Versuchen, siehe [Retry-Logik](#9-fehlerbehandlung--retry-logik))
3. Das XML auf korrekte Syntax geprüft
4. Falls eine XSD vorhanden: Schema-Validierung
5. Mit dem Referenz-XML aus `daten/testdaten/test_xml/` verglichen (strukturelle Ähnlichkeit)

```powershell
python main.py test
```

**Beispielausgabe:**

```
═════════════════════════════════════════════════════════════════
  TESTERGEBNISSE
  Gesamt        : 20
  Bestanden     : 18  ✓
  Fehlgeschlagen: 2   ✗
  Ø Ähnlichkeit : 74.3%

  Datei                                         Syntax   XSD   Ähnl.  Versuche
  ───────────────────────────────────────────── ────── ───── ─────── ────────
  ✓ LAF__TN-Bericht_Teilnehmerbericht.xlsx          ✓     –   82.1%        1
  ✓ LAF__VN_Schlussbescheid.xlsx                    ✓     –   68.4%        2
  ✗ LAF__VN_Zahlenmäßiger_Nachweis.xlsx             ✗     –       –        3
═════════════════════════════════════════════════════════════════
```

**Ausgaben:**
- Generierte XML-Dateien: `daten/ausgabe/testergebnisse/`
- Testprotokoll (Textdatei): `daten/ausgabe/testergebnisse/testbericht_YYYYMMDD_HHMMSS.txt`

---

### Schritt 4 – Excel konvertieren (finale Nutzung)

Eine beliebige LAF-Formular-Excel-Datei wird in ein XML-Dokument konvertiert.

**Vorbereitung:** Excel-Datei(en) in `daten/eingabe/` ablegen.

```powershell
# Einzelne Datei
python main.py konvertiere daten/eingabe/MeinFormular.xlsx

# Mehrere Dateien gleichzeitig
python main.py konvertiere daten/eingabe/Formular1.xlsx daten/eingabe/Formular2.xlsx

# Ganzen Ordner verarbeiten (alle .xlsx darin)
python main.py konvertiere daten/eingabe/
```

**Ausgabe:** `daten/ausgabe/<dateiname>.xml` je Eingabedatei

**Was intern passiert:**

```
1. Excel einlesen        →  ExcelData (Formularname, Zeilen, Metadaten)
2. JSON-String erzeugen  →  kompaktes JSON für den Modell-Prompt
3. Modell laden          →  Mistral-7B + LoRA-Adapter (einmalig, ca. 30–60 Sek.)
4. XML generieren        →  [INST] Konvertiere JSON → XML [/INST]
                            ↳ Bei ungültigem XML: bis zu 3× erneut versuchen
5. Syntax prüfen         →  lxml-Validierung
6. XSD prüfen            →  falls Schema in daten/schema/ vorhanden
7. Pretty-Print          →  eingerücktes XML mit UTF-8-Deklaration
8. Speichern             →  daten/ausgabe/<dateiname>.xml
```

---

## 6. Alle CLI-Optionen

```powershell
# Allgemeine Hilfe
python main.py --help

# Modus-spezifische Hilfe
python main.py jsonl --help
python main.py training --help
python main.py test --help
python main.py konvertiere --help
```

### Globale Optionen (vor dem Modus)

| Option | Beschreibung | Beispiel |
|---|---|---|
| `--config PFAD` | Alternative Konfigurationsdatei | `--config prod.yaml` |
| `--log-level LEVEL` | Log-Level überschreiben | `--log-level DEBUG` |

### Modus `training`

| Option | Beschreibung | Beispiel |
|---|---|---|
| `--epochs N` | Epoch-Anzahl überschreiben | `--epochs 5` |

### Modus `konvertiere`

| Option | Beschreibung | Beispiel |
|---|---|---|
| `excel_datei` | Pflicht: Pfad zur Excel-Datei | `daten/eingabe/Formular.xlsx` |
| `--ausgabe ORDNER` | Ausgabeordner überschreiben | `--ausgabe eigener/ordner` |

### Beispiele

```powershell
# JSONL mit Debug-Logging erzeugen
python main.py --log-level DEBUG jsonl

# Training mit 5 Epochs und eigener Konfiguration
python main.py --config meine_config.yaml training --epochs 5

# Testlauf
python main.py test

# Konvertierung mit eigenem Ausgabeordner
python main.py konvertiere daten/eingabe/LAF__VN_Schlussbescheid.xlsx --ausgabe Ergebnisse
```

---

## 7. Konfiguration (`config.yaml`)

Alle Parameter werden zentral in `config.yaml` verwaltet. CLI-Argumente überschreiben die YAML-Werte.

### Modell

| Parameter | Standard | Beschreibung |
|---|---|---|
| `modell_pfad` | `modell/modell_output` | Pfad zum trainierten LoRA-Adapter |
| `basis_modell` | `mistralai/Mistral-7B-Instruct-v0.3` | HuggingFace Modell-ID oder lokaler Pfad |

### Generierung

| Parameter | Standard | Beschreibung |
|---|---|---|
| `max_new_tokens` | `4096` | Maximale Anzahl generierter Token pro Anfrage |
| `temperature` | `0.3` | Sampling-Temperatur (0.0 = deterministisch, 1.0 = kreativ) |
| `top_p` | `0.95` | Nucleus-Sampling-Schwellwert |
| `retries` | `3` | Maximale Wiederholungen bei ungültigem XML |

### Pfade – Trainingsdaten

| Parameter | Standard | Beschreibung |
|---|---|---|
| `trainingsdaten_excel` | `daten/trainingsdaten/eingabe_excel` | Excel-Eingabe für das Training |
| `trainingsdaten_erzeugte_json` | `daten/trainingsdaten/erzeugte_json` | JSON automatisch aus Excel erzeugt |
| `trainingsdaten_xml` | `daten/trainingsdaten/eingabe_xml` | Referenz-XML (Soll-Ausgabe) |
| `jsonl_pfad` | `daten/trainingsdaten/jsonl/training_data_json.jsonl` | JSONL-Ausgabedatei |

### Pfade – Testdaten

| Parameter | Standard | Beschreibung |
|---|---|---|
| `testdaten_excel` | `daten/testdaten/test_excel` | Excel-Eingabe für den Testmodus |
| `testdaten_erzeugte_json` | `daten/testdaten/erzeugte_json` | JSON automatisch aus Excel erzeugt |
| `testdaten_xml` | `daten/testdaten/test_xml` | Referenz-XML für den Vergleich |

### Pfade – Finale Nutzung

| Parameter | Standard | Beschreibung |
|---|---|---|
| `ausgabe_pfad` | `daten/ausgabe` | Zielordner für generierte XML-Dateien |
| `schema_pfad` | `daten/schema` | Ordner für XSD-Schema (optional) |

### Training

| Parameter | Standard | Beschreibung |
|---|---|---|
| `num_train_epochs` | `3` | Anzahl vollständiger Durchläufe durch den Trainingsdatensatz (mehr = länger, aber besser bis zum Overfitting-Punkt) |
| `batch_size` | `4` | Batch-Größe pro GPU |
| `learning_rate` | `0.0002` | Lernrate (Adam-Optimizer) |
| `lora_r` | `16` | LoRA Rang (Adapter-Komplexität) |
| `lora_alpha` | `32` | LoRA Skalierungsfaktor |
| `lora_dropout` | `0.05` | Dropout-Rate im LoRA-Adapter |
| `gradient_accumulation_steps` | `4` | Gradientenakkumulation (effektiver Batch = 4×4=16) |
| `max_seq_length` | `2048` | Maximale Token-Länge pro Trainingsbeispiel |

### Logging

| Parameter | Standard | Beschreibung |
|---|---|---|
| `log_level` | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |
| `log_datei` | `pipeline.log` | Pfad zur Logdatei (neben `main.py`) |

---

## 8. Datenstruktur & Eingabeformat

### LAF-Formular-Excel-Format

Das Programm erwartet Excel-Dateien im **LAF-Formularformat** mit folgender Struktur:

| Zeile | Spalte A | Spalte B |
|---|---|---|
| 1 | `Formularname:` | Name des Formulars |
| 2 | (leer) | |
| 3 | `Dateiname:` | Technischer Dateiname |
| 4 | **Kopfzeile** | Gliederung / Descriptor / Label / ... |
| 5+ | **Datensätze** | je eine Zeile pro Formularelement |

**Datenspalten ab Zeile 5:**

| Spalte | Feldname | Beschreibung |
|---|---|---|
| A | `gliederung` | Strukturebene (Seite / Block / Descriptor) |
| B | `descriptor` | Technischer Bezeichner des Feldes |
| C | `label` | Anzeigename des Feldes |
| D | `alternatives_label` | Alternativer Anzeigename |
| E | `pflichtfeld` | Pflichtfeld-Kennzeichnung (`o` = ja) |
| F | `schreibgeschuetzt` | Schreibschutz (`x` = ja) |

### Trainingsdaten hinzufügen

Neue Trainingspaare können jederzeit hinzugefügt werden:

1. Excel-Datei nach `daten/trainingsdaten/eingabe_excel/` kopieren
2. Zugehörige Referenz-XML nach `daten/trainingsdaten/eingabe_xml/` kopieren *(gleicher Dateiname, Endung `.xml`)*
3. `python main.py jsonl` ausführen → JSON + JSONL werden automatisch erzeugt
4. `python main.py training` ausführen → Modell neu trainieren

### Testdaten hinzufügen

1. Excel-Datei nach `daten/testdaten/test_excel/` kopieren
2. Optional: Referenz-XML nach `daten/testdaten/test_xml/` kopieren *(für Ähnlichkeitsvergleich)*
3. `python main.py test` ausführen

---

## 9. Fehlerbehandlung & Retry-Logik

### Retry bei ungültigem XML

Falls das Modell kein syntaktisch korrektes XML generiert, wird der Vorgang automatisch wiederholt. Die Anzahl der Versuche ist über `retries` in `config.yaml` konfigurierbar (Standard: **3**).

```
Versuch 1 → XML generieren → Syntax prüfen → ungültig → Warnung loggen
Versuch 2 → XML generieren → Syntax prüfen → ungültig → Warnung loggen
Versuch 3 → XML generieren → Syntax prüfen → ungültig → ABBRUCH + Fehler loggen
```

Nach dem letzten fehlgeschlagenen Versuch wird der Fehler in `pipeline.log` protokolliert und das Programm beendet sich mit Exit-Code `2`.

### Fehlerverhalten nach Fehlerart

| Fehlerfall | Verhalten | Exit-Code |
|---|---|---|
| `config.yaml` nicht gefunden | Sofortiger Abbruch, Meldung auf Konsole | `1` |
| Pflichtfeld in `config.yaml` fehlt | Sofortiger Abbruch mit Liste fehlender Felder | `1` |
| Excel-Datei nicht gefunden | Abbruch, Fehlermeldung | `1` |
| Excel-Datei korrupt / falsches Format | Abbruch, Fehlermeldung | `1` |
| KI-Modell nicht ladbar | Abbruch, Fehlermeldung | `1` |
| LoRA-Adapter nicht gefunden | **Warnung**, automatischer Fallback auf Basis-Modell | – |
| XML nach 3 Versuchen ungültig | Abbruch, Fehlermeldung in Log | `2` |
| XSD-Validierung fehlgeschlagen | **Warnung** (kein Abbruch), XML wird trotzdem gespeichert | `0` |

> **Hinweis Fallback-Modell:** Wenn kein trainierter LoRA-Adapter unter `modell/modell_output/` gefunden wird (z.B. vor dem ersten Training), läuft das Programm automatisch mit dem nicht-feinabgestimmten Basis-Modell. Die Ausgabequalität ist in diesem Fall deutlich geringer. Eine entsprechende Warnung erscheint in der Konsole und im Log.

---

## 10. XSD-Schema-Validierung

Die XSD-Validierung ist **optional** und wird automatisch aktiviert, sobald eine `.xsd`-Datei im Schema-Ordner liegt.

### XSD-Datei hinzufügen

```
daten/schema/
└── mein_schema.xsd    ← Datei hier ablegen
```

Das Programm erkennt die erste gefundene `.xsd`-Datei automatisch – keine Konfigurationsänderung nötig.

### Verhalten mit XSD

- **Konvertierungsmodus:** Bei Schema-Verletzung wird eine Warnung ausgegeben, das XML aber trotzdem gespeichert.
- **Testmodus:** Die XSD-Prüfung erscheint als eigene Spalte im Ergebnisbericht.
- **Ohne XSD:** Nur Syntax-Validierung; kein Fehler.

---

## 11. Testmodus im Detail

Der Testmodus (`python main.py test`) dient zur Qualitätssicherung des trainierten Modells.

### Bewertungskriterien

| Kriterium | Pflicht | Beschreibung |
|---|---|---|
| Excel einlesbar | ✅ Ja | Datei muss korrekt gelesen werden können |
| XML wird generiert | ✅ Ja | Modell muss innerhalb der Retry-Versuche XML ausgeben |
| XML syntax-korrekt | ✅ Ja | Wohlgeformtes XML (lxml-Prüfung) |
| XSD-konform | ⬜ Optional | Nur wenn XSD in `daten/schema/` vorhanden |
| Ähnlichkeit ≥ 50% | ⬜ Optional | Vergleich mit Referenz-XML (SequenceMatcher) |

Ein Test gilt als **bestanden**, wenn die ersten drei Pflichtkriterien erfüllt sind.

### Ähnlichkeitsberechnung

Die strukturelle Ähnlichkeit zwischen generiertem und Referenz-XML wird mit dem `difflib.SequenceMatcher` berechnet (Wertebereich 0 % – 100 %). Ein Wert von 50 % wird intern als Schwellwert für „inhaltlich korrekt" gewertet, beeinflusst aber nicht das Pass/Fail-Ergebnis.

### Ausgabedateien

| Datei | Beschreibung |
|---|---|
| `daten/ausgabe/testergebnisse/*.xml` | Generierte XML-Dateien je Testdatei |
| `daten/ausgabe/testergebnisse/testbericht_*.txt` | Textprotokoll mit allen Einzelergebnissen |

---

## 12. Architektur & Module

```
main.py
  │
  ├── core/config.py          → AppConfig aus config.yaml laden
  ├── core/logger.py          → Logging initialisieren
  │
  ├── [Modus: jsonl]
  │     └── core/jsonl_ersteller.py   JSON + XML → JSONL
  │
  ├── [Modus: training]
  │     └── core/trainer.py           QLoRA Fine-Tuning
  │
  ├── [Modus: test]
  │     └── core/tester.py            Automatisierter Testlauf
  │           ├── core/excel_parser.py
  │           ├── core/ki_generator.py
  │           └── core/xml_validator.py
  │
  └── [Modus: konvertiere]
        ├── core/excel_parser.py      Excel → ExcelData
        ├── core/ki_generator.py      ExcelData → XML (mit Retry)
        ├── core/xml_validator.py     Syntax + XSD prüfen, Pretty-Print
        └── core/file_writer.py       XML speichern
```

Eine ausführliche technische Beschreibung jedes Moduls, der Datenklassen und Schnittstellen befindet sich in [`docs/ARCHITEKTUR.md`](docs/ARCHITEKTUR.md).

---

## 13. Häufige Fehler & Lösungen

### `Konfigurationsdatei nicht gefunden`

```
[FEHLER] Konfiguration: Konfigurationsdatei nicht gefunden: ...
```

**Ursache:** `main.py` und `config.yaml` liegen nicht im selben Ordner, oder das Terminal-Arbeitsverzeichnis ist falsch.

**Lösung:**
```powershell
cd "C:\...\excel_zu_xml"
python main.py ...
```

---

### `CUDA not available` / Training sehr langsam

**Ursache:** PyTorch findet keine GPU.

**Prüfen:**
```powershell
python -c "import torch; print(torch.cuda.is_available())"
```

**Lösung:** PyTorch mit korrekter CUDA-Version neu installieren (siehe [Installation](#4-installation)).

---

### `LoRA-Adapter nicht gefunden` (Warnung)

```
WARNING  LoRA-Adapter nicht gefunden (modell/modell_output). Fallback auf Basis-Modell
```

**Ursache:** Das Training wurde noch nicht durchgeführt, oder `modell_pfad` in `config.yaml` zeigt auf den falschen Ordner.

**Lösung:** Zuerst `python main.py training` ausführen, oder `modell_pfad` in `config.yaml` korrigieren.

---

### `Nach 3 Versuchen kein gültiges XML erzeugt`

**Ursache:** Das Modell generiert kein wohlgeformtes XML. Mögliche Gründe:
- Modell noch nicht oder unzureichend trainiert
- `temperature` zu hoch (zu viel Zufälligkeit)
- `max_new_tokens` zu gering für die Dateigröße

**Lösung:**
1. `temperature` in `config.yaml` auf `0.1` reduzieren
2. `max_new_tokens` erhöhen (z.B. `8192`)
3. Mehr Trainings-Epochs durchführen (`--epochs 5`)
4. Trainingsdaten auf Qualität prüfen

---

### `Excel-Datei konnte nicht geöffnet werden`

**Ursache:** Datei ist beschädigt, passwortgeschützt oder kein gültiges `.xlsx`-Format.

**Lösung:** Datei in Excel öffnen, als `.xlsx` speichern und erneut versuchen.

---

### Virtuelle Umgebung nicht aktiv

```
ModuleNotFoundError: No module named 'openpyxl'
```

**Lösung:**
```powershell
.\venv\Scripts\Activate.ps1
```
