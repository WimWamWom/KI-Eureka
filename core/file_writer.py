"""Speichert das generierte XML in den konfigurierten Ausgabeordner."""

from __future__ import annotations

from pathlib import Path


def speichere_xml(xml_string: str, eingabe_pfad: str, ausgabe_ordner: str) -> str:
    """
    Schreibt das XML in den Ausgabeordner.
    Dateiname = Stamm der Eingabedatei + .xml

    Returns:
        Absoluter Pfad zur gespeicherten XML-Datei.
    """
    ziel_ordner = Path(ausgabe_ordner).resolve()
    ziel_ordner.mkdir(parents=True, exist_ok=True)

    dateiname = Path(eingabe_pfad).stem + ".xml"
    ziel_pfad = ziel_ordner / dateiname

    with open(ziel_pfad, "w", encoding="utf-8") as f:
        f.write(xml_string)

    return str(ziel_pfad)

