"""Lädt die Konfiguration aus config.yaml und stellt sie als Dataclass bereit."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class AppConfig:
    # Modell
    modell_pfad: str
    basis_modell: str

    # Generierung
    max_new_tokens: int
    temperature: float
    top_p: float

    # Fehlerbehandlung
    retries: int

    # Pfade – Trainingsdaten
    trainingsdaten_excel: str       # Excel-Eingabe für Training
    trainingsdaten_erzeugte_json: str  # JSON aus Excel (automatisch erzeugt)
    trainingsdaten_xml: str         # Referenz-XML für Training
    jsonl_pfad: str                 # Ausgabe-JSONL

    # Pfade – Testdaten
    testdaten_excel: str            # Excel-Eingabe für Test
    testdaten_erzeugte_json: str    # JSON aus Excel (automatisch erzeugt)
    testdaten_xml: str              # Referenz-XML für Vergleich

    # Pfade – Finale Nutzung
    ausgabe_pfad: str               # Ausgabe der KI
    schema_pfad: str                # Ordner mit optionaler XSD-Datei

    # Training
    lora_r: int
    lora_alpha: int
    lora_dropout: float
    learning_rate: float
    batch_size: int
    gradient_accumulation_steps: int
    num_train_epochs: int
    max_seq_length: int

    # Logging
    log_level: str
    log_datei: str

    # Abgeleitete absolute Pfade (nicht in YAML)
    modell_pfad_absolut: Path = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.modell_pfad_absolut = Path(self.modell_pfad).resolve()


_PFLICHTFELDER: dict = {
    "modell_pfad": str,
    "basis_modell": str,
    "max_new_tokens": int,
    "temperature": float,
    "top_p": float,
    "retries": int,
    "ausgabe_pfad": str,
    "trainingsdaten_excel": str,
    "trainingsdaten_erzeugte_json": str,
    "trainingsdaten_xml": str,
    "jsonl_pfad": str,
    "testdaten_excel": str,
    "testdaten_erzeugte_json": str,
    "testdaten_xml": str,
    "schema_pfad": str,
    "lora_r": int,
    "lora_alpha": int,
    "lora_dropout": float,
    "learning_rate": float,
    "batch_size": int,
    "gradient_accumulation_steps": int,
    "num_train_epochs": int,
    "max_seq_length": int,
    "log_level": str,
    "log_datei": str,
}

_STANDARDWERTE: dict = {
    "top_p": 0.95,
    "log_level": "INFO",
    "log_datei": "pipeline.log",
    "schema_pfad": "daten/schema",
    "trainingsdaten_excel": "daten/trainingsdaten/eingabe_excel",
    "trainingsdaten_erzeugte_json": "daten/trainingsdaten/erzeugte_json",
    "trainingsdaten_xml": "daten/trainingsdaten/eingabe_xml",
    "jsonl_pfad": "daten/trainingsdaten/jsonl/training_data_json.jsonl",
    "testdaten_excel": "daten/testdaten/test_excel",
    "testdaten_erzeugte_json": "daten/testdaten/erzeugte_json",
    "testdaten_xml": "daten/testdaten/test_xml",
    "ausgabe_pfad": "daten/ausgabe",
    "lora_r": 16,
    "lora_alpha": 32,
    "lora_dropout": 0.05,
    "learning_rate": 2e-4,
    "batch_size": 4,
    "gradient_accumulation_steps": 4,
    "num_train_epochs": 3,
    "max_seq_length": 2048,
}


def lade_config(pfad: str = "config.yaml") -> AppConfig:
    """Lädt config.yaml und gibt eine validierte AppConfig zurück."""
    config_pfad = Path(pfad).resolve()
    if not config_pfad.exists():
        raise FileNotFoundError(f"Konfigurationsdatei nicht gefunden: {config_pfad}")

    with open(config_pfad, encoding="utf-8") as f:
        roh: dict = yaml.safe_load(f) or {}

    for schluessel, wert in _STANDARDWERTE.items():
        roh.setdefault(schluessel, wert)

    fehlend = [k for k in _PFLICHTFELDER if k not in roh]
    if fehlend:
        raise ValueError(f"Fehlende Pflichtfelder in {pfad}: {fehlend}")

    kwargs = {k: typ(roh[k]) for k, typ in _PFLICHTFELDER.items()}
    return AppConfig(**kwargs)

