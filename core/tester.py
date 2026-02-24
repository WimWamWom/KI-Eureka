"""
Testmodus: Prüft die KI anhand vorhandener Testdaten.

Ablauf für jede Excel in daten/testdaten/test_excel/:
  1. Excel einlesen → JSON in testdaten/erzeugte_json/ speichern
  2. KI generiert XML (mit Retry-Logik)
  3. XML-Syntax prüfen
  4. Optional: XSD-Validierung falls Schema vorhanden
  5. Optional: Inhaltlicher Vergleich mit Referenz-XML aus testdaten/test_xml/
  6. Ergebnis protokollieren

Ausgabe: Konsolenbericht + XML + Protokoll in daten/ausgabe/testergebnisse/
"""

from __future__ import annotations

import difflib
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .config import AppConfig
from .excel_parser import parse_excel, ExcelParseError
from .file_writer import speichere_xml
from .ki_generator import KIGenerator, XMLGenerierungFehler
from .xml_validator import (
    lade_xsd_schema,
    pretty_print_xml,
    validiere_gegen_xsd,
    validiere_xml,
)

logger = logging.getLogger(__name__)


@dataclass
class Testergebnis:
    """Ergebnis eines einzelnen Tests."""

    dateiname: str
    excel_gelesen: bool = False
    xml_generiert: bool = False
    syntax_ok: bool = False
    xsd_ok: Optional[bool] = None          # None = kein Schema vorhanden
    inhalt_ok: Optional[bool] = None       # None = kein Referenz-XML vorhanden
    aehnlichkeit: Optional[float] = None   # 0.0 – 1.0
    fehler: Optional[str] = None
    versuche: int = 0                      # Wie viele Generierungsversuche nötig waren

    @property
    def bestanden(self) -> bool:
        """Test gilt als bestanden wenn Syntax korrekt ist (XSD/Inhalt optional)."""
        return self.excel_gelesen and self.xml_generiert and self.syntax_ok


@dataclass
class Testbericht:
    """Gesamtbericht über alle Tests."""

    ergebnisse: list[Testergebnis] = field(default_factory=list)

    @property
    def gesamt(self) -> int:
        return len(self.ergebnisse)

    @property
    def bestanden(self) -> int:
        return sum(1 for e in self.ergebnisse if e.bestanden)

    @property
    def fehlgeschlagen(self) -> int:
        return self.gesamt - self.bestanden

    @property
    def xsd_geprueft(self) -> int:
        return sum(1 for e in self.ergebnisse if e.xsd_ok is not None)

    @property
    def xsd_bestanden(self) -> int:
        return sum(1 for e in self.ergebnisse if e.xsd_ok is True)

    @property
    def durchschnittliche_aehnlichkeit(self) -> Optional[float]:
        werte = [e.aehnlichkeit for e in self.ergebnisse if e.aehnlichkeit is not None]
        return sum(werte) / len(werte) if werte else None


def _berechne_aehnlichkeit(xml_generiert: str, xml_referenz: str) -> float:
    """Berechnet strukturelle Ähnlichkeit zweier XML-Strings (0.0–1.0)."""
    return difflib.SequenceMatcher(
        None,
        xml_generiert.strip(),
        xml_referenz.strip(),
    ).ratio()


def _drucke_bericht(bericht: Testbericht) -> None:
    """Gibt den formatierten Testbericht auf der Konsole aus."""
    trenn = "=" * 65
    print(f"\n{trenn}")
    print("  TESTERGEBNISSE")
    print(trenn)
    print(f"  Gesamt        : {bericht.gesamt}")
    print(f"  Bestanden     : {bericht.bestanden}  ✓")
    print(f"  Fehlgeschlagen: {bericht.fehlgeschlagen}  ✗")

    if bericht.xsd_geprueft > 0:
        print(f"  XSD-geprüft   : {bericht.xsd_geprueft}  "
              f"(davon OK: {bericht.xsd_bestanden})")

    if bericht.durchschnittliche_aehnlichkeit is not None:
        print(f"  Ø Ähnlichkeit : {bericht.durchschnittliche_aehnlichkeit:.1%}")

    print(f"\n  {'Datei':<45} {'Syntax':>6} {'XSD':>5} {'Ähnl.':>7} {'Versuche':>8}")
    print(f"  {'-'*45} {'-'*6} {'-'*5} {'-'*7} {'-'*8}")

    for e in bericht.ergebnisse:
        syntax  = "✓" if e.syntax_ok else "✗"
        xsd     = ("✓" if e.xsd_ok else "✗") if e.xsd_ok is not None else "–"
        aehnl   = f"{e.aehnlichkeit:.1%}" if e.aehnlichkeit is not None else "–"
        versuche = str(e.versuche) if e.versuche > 0 else "–"
        status  = "✓" if e.bestanden else "✗"
        name    = e.dateiname[:43]
        print(f"  {status} {name:<43} {syntax:>6} {xsd:>5} {aehnl:>7} {versuche:>8}")
        if e.fehler and not e.bestanden:
            print(f"    → {e.fehler[:80]}")

    print(trenn)


def teste_modell(config: AppConfig) -> Testbericht:
    """
    Führt den vollständigen Testlauf durch.

    Liest alle Excel-Dateien aus daten/testdaten/test_excel/,
    lässt die KI XML generieren und vergleicht mit Referenz-XMLs
    aus daten/testdaten/test_xml/.

    Returns:
        Testbericht mit allen Einzelergebnissen.
    """
    basis = Path(__file__).resolve().parent.parent

    test_excel_ordner      = Path(config.testdaten_excel).resolve()
    test_json_ordner       = Path(config.testdaten_erzeugte_json).resolve()
    test_referenz_ordner   = Path(config.testdaten_xml).resolve()
    ausgabe_ordner         = basis / "daten" / "ausgabe" / "testergebnisse"

    test_json_ordner.mkdir(parents=True, exist_ok=True)
    ausgabe_ordner.mkdir(parents=True, exist_ok=True)

    # XSD-Schema laden (optional)
    xsd_schema = lade_xsd_schema(config.schema_pfad)
    if xsd_schema:
        logger.info("XSD-Schema geladen aus: %s", config.schema_pfad)
    else:
        logger.info("Kein XSD-Schema gefunden – nur Syntax-Validierung.")

    # Testdateien ermitteln
    excel_dateien = sorted(test_excel_ordner.glob("*.xlsx")) + sorted(test_excel_ordner.glob("*.xls"))
    if not excel_dateien:
        logger.warning("Keine Excel-Dateien in %s gefunden.", test_excel_ordner)
        return Testbericht()

    logger.info("%d Testdatei(en) gefunden.", len(excel_dateien))

    # Modell einmalig laden
    logger.info("Lade KI-Modell …")
    try:
        generator = KIGenerator(config)
    except Exception as exc:
        logger.error("Modell konnte nicht geladen werden: %s", exc)
        raise

    bericht = Testbericht()

    for excel_pfad in excel_dateien:
        ergebnis = Testergebnis(dateiname=excel_pfad.name)
        logger.info("─── Teste: %s", excel_pfad.name)

        # 1. Excel einlesen + JSON speichern
        try:
            excel_data = parse_excel(str(excel_pfad))
            ergebnis.excel_gelesen = True
            # JSON in erzeugte_json/ ablegen
            json_ziel = test_json_ordner / (excel_pfad.stem + ".json")
            json_ziel.write_text(excel_data.zu_json_string(), encoding="utf-8")
        except ExcelParseError as exc:
            ergebnis.fehler = f"Excel-Parse-Fehler: {exc}"
            logger.error("  ✗ Excel: %s", exc)
            bericht.ergebnisse.append(ergebnis)
            continue

        # 2. XML generieren (Retry-Logik im KIGenerator)
        xml_roh: Optional[str] = None
        for versuch in range(1, config.retries + 1):
            ergebnis.versuche = versuch
            try:
                xml_roh = generator.generiere_xml(excel_data)
                ergebnis.xml_generiert = True
                break
            except XMLGenerierungFehler as exc:
                ergebnis.fehler = f"Generierung fehlgeschlagen: {exc}"
                logger.error("  ✗ Generierung: %s", exc)
                break

        if not ergebnis.xml_generiert or xml_roh is None:
            bericht.ergebnisse.append(ergebnis)
            continue

        # 3. Syntax-Validierung
        syntax_ok, syntax_fehler = validiere_xml(xml_roh)
        ergebnis.syntax_ok = syntax_ok
        if not syntax_ok:
            ergebnis.fehler = f"XML-Syntaxfehler: {syntax_fehler}"
            logger.warning("  ✗ Syntax: %s", syntax_fehler)
            bericht.ergebnisse.append(ergebnis)
            continue

        # XML pretty-printen und speichern
        try:
            xml_formatiert = pretty_print_xml(xml_roh)
        except ValueError:
            xml_formatiert = xml_roh

        speichere_xml(xml_formatiert, str(excel_pfad), str(ausgabe_ordner))

        # 4. XSD-Validierung (optional)
        if xsd_schema:
            xsd_ok, xsd_fehler = validiere_gegen_xsd(xml_roh, xsd_schema)
            ergebnis.xsd_ok = xsd_ok
            if not xsd_ok:
                logger.warning("  ✗ XSD: %s", xsd_fehler)
            else:
                logger.info("  ✓ XSD")

        # 5. Inhaltlicher Vergleich mit Referenz-XML aus test_xml/
        referenz_pfad = test_referenz_ordner / (excel_pfad.stem + ".xml")
        if referenz_pfad.exists():
            referenz_xml = referenz_pfad.read_text(encoding="utf-8")
            aehnlichkeit = _berechne_aehnlichkeit(xml_formatiert, referenz_xml)
            ergebnis.aehnlichkeit = aehnlichkeit
            ergebnis.inhalt_ok = aehnlichkeit >= 0.5
            logger.info("  Ähnlichkeit mit Referenz: %.1f%%", aehnlichkeit * 100)
        else:
            logger.info("  Kein Referenz-XML in test_xml/ für '%s'.", excel_pfad.stem)

        status = "✓" if ergebnis.bestanden else "✗"
        logger.info("  %s Ergebnis: %s", status, excel_pfad.name)
        bericht.ergebnisse.append(ergebnis)

    return bericht

