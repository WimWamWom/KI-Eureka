"""Zentrale Datenstrukturen der Pipeline."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Optional


@dataclass
class ExcelData:
    """Repräsentiert den bereinigten Inhalt einer LAF-Excel-Datei."""

    formularname: str
    dateiname: str
    blattname: str
    zeilen: list[dict]

    def zu_json_string(self) -> str:
        """Serialisiert die Daten als kompakten JSON-String für den Modell-Prompt."""
        payload = {
            "formularname": self.formularname,
            "dateiname": self.dateiname,
            "blattname": self.blattname,
            "zeilen": self.zeilen,
        }
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


@dataclass
class ConversionResult:
    """Ergebnis einer einzelnen Excel-zu-XML-Konvertierung."""

    eingabe_pfad: str
    erfolg: bool
    ausgabe_pfad: Optional[str] = None
    xml_inhalt: Optional[str] = None
    fehler: Optional[str] = None

