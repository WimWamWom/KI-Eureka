"""
Erstellt JSONL-Trainingsdaten.

Ablauf:
  1. Excel-Dateien aus trainingsdaten/eingabe_excel/ einlesen
  2. Jede Excel → JSON-String (via ExcelData.zu_json_string())
  3. JSON in trainingsdaten/erzeugte_json/ speichern
  4. JSON + passendes Referenz-XML → JSONL-Trainingspaare
  5. JSONL nach trainingsdaten/jsonl/ schreiben
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from .config import AppConfig
from .excel_parser import parse_excel, ExcelParseError

logger = logging.getLogger(__name__)


def _excel_zu_json_dateien(excel_ordner: Path, json_ordner: Path) -> list[Path]:
    """
    Liest alle Excel-Dateien aus excel_ordner, erzeugt JSON-Dateien in json_ordner.
    Gibt Liste der erzeugten JSON-Pfade zurück.
    """
    json_ordner.mkdir(parents=True, exist_ok=True)
    excel_dateien = sorted(excel_ordner.glob("*.xlsx")) + sorted(excel_ordner.glob("*.xls"))

    if not excel_dateien:
        logger.warning("Keine Excel-Dateien in: %s", excel_ordner)
        return []

    erzeugte: list[Path] = []
    for excel_pfad in excel_dateien:
        try:
            excel_data = parse_excel(str(excel_pfad))
            json_inhalt = excel_data.zu_json_string()
            json_ziel = json_ordner / (excel_pfad.stem + ".json")
            json_ziel.write_text(json_inhalt, encoding="utf-8")
            erzeugte.append(json_ziel)
            logger.debug("JSON erzeugt: %s", json_ziel.name)
        except ExcelParseError as exc:
            logger.warning("Überspringe '%s': %s", excel_pfad.name, exc)

    logger.info("%d JSON-Dateien aus Excel erzeugt in: %s", len(erzeugte), json_ordner)
    return erzeugte


def erstelle_jsonl(config: AppConfig) -> int:
    """
    Vollständiger JSONL-Erzeugungsprozess:
      Excel → JSON (erzeugte_json/) → JSONL (jsonl/)

    Returns:
        Anzahl der erzeugten Trainingspaare.
    """
    excel_ordner = Path(config.trainingsdaten_excel).resolve()
    json_ordner  = Path(config.trainingsdaten_erzeugte_json).resolve()
    xml_ordner   = Path(config.trainingsdaten_xml).resolve()
    jsonl_ziel   = Path(config.jsonl_pfad).resolve()

    if not excel_ordner.exists():
        raise FileNotFoundError(f"Excel-Eingabeordner nicht gefunden: {excel_ordner}")
    if not xml_ordner.exists():
        raise FileNotFoundError(f"XML-Eingabeordner nicht gefunden: {xml_ordner}")

    # Schritt 1: Excel → JSON
    _excel_zu_json_dateien(excel_ordner, json_ordner)

    # Schritt 2: JSON + XML → JSONL
    json_dateien = {p.stem: p for p in json_ordner.glob("*.json")}
    xml_dateien  = {p.stem: p for p in xml_ordner.glob("*.xml")}

    gemeinsame_stems = sorted(set(json_dateien) & set(xml_dateien))
    fehlend_xml  = sorted(set(json_dateien) - set(xml_dateien))
    fehlend_json = sorted(set(xml_dateien)  - set(json_dateien))

    if fehlend_xml:
        logger.warning("Kein Referenz-XML für: %s", fehlend_xml)
    if fehlend_json:
        logger.warning("Keine JSON/Excel für XML-Dateien: %s", fehlend_json)

    jsonl_ziel.parent.mkdir(parents=True, exist_ok=True)
    eintraege: list[dict] = []

    for stem in gemeinsame_stems:
        try:
            json_inhalt = json_dateien[stem].read_text(encoding="utf-8").strip()
            xml_inhalt  = xml_dateien[stem].read_text(encoding="utf-8").strip()
            json.loads(json_inhalt)  # Validierung
            eintraege.append({"id": stem, "prompt": json_inhalt, "completion": xml_inhalt})
        except Exception as exc:
            logger.warning("Überspringe '%s': %s", stem, exc)

    with open(jsonl_ziel, "w", encoding="utf-8") as f:
        for eintrag in eintraege:
            f.write(json.dumps(eintrag, ensure_ascii=False) + "\n")

    logger.info("JSONL erstellt: %s (%d Einträge)", jsonl_ziel, len(eintraege))
    return len(eintraege)

