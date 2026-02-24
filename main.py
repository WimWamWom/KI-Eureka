"""
main.py – Einstiegspunkt der Excel-zu-XML-Pipeline.

Modi:
  jsonl       – JSONL-Trainingsdaten aus JSON + XML erzeugen
  training    – Mistral-7B fine-tunen (QLoRA)
  test        – KI anhand vorhandener Testdaten prüfen
  konvertiere – Excel-Datei → XML (finale Nutzung)

Verwendung:
  python main.py jsonl
  python main.py training
  python main.py training --epochs 5
  python main.py test
  python main.py konvertiere daten/eingabe/meine_datei.xlsx
  python main.py konvertiere daten/eingabe/meine_datei.xlsx --ausgabe daten/ausgabe
"""

from __future__ import annotations

import argparse
import logging
import sys

from core.config import lade_config
from core.logger import setup_logger

logger = logging.getLogger(__name__)


# ────────────────────────────────────────────────────────────────
# Argument-Parser
# ────────────────────────────────────────────────────────────────

def _erstelle_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="Excel → XML Pipeline mit KI-Unterstützung (Mistral-7B)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Beispiele:\n"
            "  python main.py jsonl\n"
            "  python main.py training\n"
            "  python main.py training --epochs 5\n"
            "  python main.py test\n"
            "  python main.py konvertiere daten/eingabe/Formular.xlsx\n"
            "  python main.py konvertiere daten/eingabe/Formular.xlsx --ausgabe daten/ausgabe\n"
        ),
    )
    parser.add_argument(
        "--config",
        default="config.yaml",
        metavar="PFAD",
        help="Pfad zur Konfigurationsdatei (Standard: config.yaml)",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        metavar="LEVEL",
        help="Log-Level überschreiben (DEBUG | INFO | WARNING | ERROR)",
    )

    sub = parser.add_subparsers(dest="modus", required=True)

    # ── Modus: jsonl ──────────────────────────────────────────
    sub.add_parser(
        "jsonl",
        help="JSONL-Trainingsdaten aus JSON + XML erzeugen",
    )

    # ── Modus: training ───────────────────────────────────────
    p_train = sub.add_parser(
        "training",
        help="Mistral-7B fine-tunen (QLoRA)",
    )
    p_train.add_argument(
        "--epochs",
        type=int,
        metavar="N",
        help="Anzahl Trainings-Epochs (überschreibt config.yaml)",
    )

    # ── Modus: test ───────────────────────────────────────────
    sub.add_parser(
        "test",
        help=(
            "KI anhand vorhandener Testdaten prüfen: "
            "Excel aus daten/testdaten/ → XML generieren → "
            "Syntax/XSD/Inhalt validieren"
        ),
    )

    # ── Modus: konvertiere ────────────────────────────────────
    p_konv = sub.add_parser(
        "konvertiere",
        help="Eine oder mehrere Excel-Dateien in XML konvertieren (finale Nutzung)",
    )
    p_konv.add_argument(
        "excel_eingabe",
        nargs="+",
        help=(
            "Pfad zu einer oder mehreren Excel-Dateien (.xlsx), "
            "oder ein Ordner (alle .xlsx darin werden verarbeitet)"
        ),
    )
    p_konv.add_argument(
        "--ausgabe",
        metavar="ORDNER",
        help="Ausgabeordner (überschreibt config.yaml)",
    )

    return parser


# ────────────────────────────────────────────────────────────────
# Modi
# ────────────────────────────────────────────────────────────────

def _modus_jsonl(config) -> int:
    """Erzeugt die JSONL-Trainingsdatei."""
    from core.jsonl_ersteller import erstelle_jsonl

    logger.info("Modus: JSONL erzeugen")
    try:
        anzahl = erstelle_jsonl(config)
        print(f"\n✓ JSONL erzeugt – {anzahl} Trainingspaare")
        print(f"  → {config.jsonl_pfad}")
        return 0
    except Exception as exc:
        logger.error("JSONL-Erzeugung fehlgeschlagen: %s", exc)
        return 1


def _modus_training(config, epochs: int | None) -> int:
    """Führt das Fine-Tuning durch."""
    from core.trainer import trainiere_modell

    if epochs is not None:
        config.num_train_epochs = epochs

    logger.info("Modus: Training (%d Epochs)", config.num_train_epochs)
    print(f"\n{'='*60}")
    print("  TRAINING STARTEN")
    print(f"  Basis-Modell : {config.basis_modell}")
    print(f"  Epochs       : {config.num_train_epochs}")
    print(f"  JSONL        : {config.jsonl_pfad}")
    print(f"{'='*60}\n")

    try:
        ausgabe = trainiere_modell(config)
        print(f"\n✓ Training abgeschlossen")
        print(f"  → Modell gespeichert: {ausgabe}")
        return 0
    except Exception as exc:
        logger.error("Training fehlgeschlagen: %s", exc)
        return 1


def _modus_test(config) -> int:
    """Testet die KI anhand aller Dateien in daten/testdaten/."""
    from core.tester import teste_modell, _drucke_bericht

    logger.info("Modus: Test")
    print(f"\n{'='*65}")
    print("  TESTMODUS")
    print(f"  Test-Excel  : {config.testdaten_excel}")
    print(f"  Referenz-XML: {config.testdaten_xml}")
    schema_info = config.schema_pfad if config.schema_pfad else "keines"
    print(f"  XSD-Schema  : {schema_info}")
    print(f"{'='*65}\n")

    try:
        bericht = teste_modell(config)
    except Exception as exc:
        logger.error("Testlauf abgebrochen: %s", exc)
        return 1

    _drucke_bericht(bericht)

    # Testergebnisse als Text-Datei speichern
    from pathlib import Path
    import datetime
    protokoll_ordner = Path("daten/ausgabe/testergebnisse")
    protokoll_ordner.mkdir(parents=True, exist_ok=True)
    zeitstempel = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    protokoll_pfad = protokoll_ordner / f"testbericht_{zeitstempel}.txt"

    with open(protokoll_pfad, "w", encoding="utf-8") as f:
        f.write(f"Testbericht – {zeitstempel}\n")
        f.write(f"Gesamt: {bericht.gesamt}  Bestanden: {bericht.bestanden}  "
                f"Fehlgeschlagen: {bericht.fehlgeschlagen}\n\n")
        for e in bericht.ergebnisse:
            status = "PASS" if e.bestanden else "FAIL"
            f.write(f"{status}  {e.dateiname}\n")
            f.write(f"  Syntax: {'OK' if e.syntax_ok else 'FEHLER'}")
            if e.xsd_ok is not None:
                f.write(f"  XSD: {'OK' if e.xsd_ok else 'FEHLER'}")
            if e.aehnlichkeit is not None:
                f.write(f"  Ähnlichkeit: {e.aehnlichkeit:.1%}")
            f.write(f"  Versuche: {e.versuche}\n")
            if e.fehler:
                f.write(f"  Fehler: {e.fehler}\n")
            f.write("\n")

    print(f"\n  Protokoll gespeichert: {protokoll_pfad}")
    return 0 if bericht.fehlgeschlagen == 0 else 2


def _modus_konvertiere(config, excel_eingabe: list[str], ausgabe: str | None) -> int:
    """Konvertiert eine oder mehrere Excel-Dateien in XML."""
    from pathlib import Path
    from core.excel_parser import parse_excel, ExcelParseError
    from core.ki_generator import KIGenerator, XMLGenerierungFehler
    from core.xml_validator import pretty_print_xml, lade_xsd_schema, validiere_gegen_xsd
    from core.file_writer import speichere_xml

    if ausgabe:
        config.ausgabe_pfad = ausgabe

    # Eingabeliste aufbauen – Ordner werden expandiert
    alle_dateien: list[Path] = []
    for eingabe in excel_eingabe:
        p = Path(eingabe)
        if p.is_dir():
            gefunden = sorted(p.glob("*.xlsx")) + sorted(p.glob("*.xls"))
            if not gefunden:
                logger.warning("Keine Excel-Dateien in Ordner: %s", p)
            alle_dateien.extend(gefunden)
        elif p.exists():
            alle_dateien.append(p)
        else:
            logger.error("Datei oder Ordner nicht gefunden: %s", p)
            return 1

    if not alle_dateien:
        logger.error("Keine Excel-Dateien zum Verarbeiten gefunden.")
        return 1

    print(f"\n{'='*60}")
    print("  KONVERTIERUNG")
    print(f"  Dateien : {len(alle_dateien)}")
    print(f"  Ausgabe : {config.ausgabe_pfad}")
    print(f"{'='*60}\n")

    # XSD-Schema einmalig laden
    xsd_schema = lade_xsd_schema(config.schema_pfad)
    if xsd_schema:
        logger.info("XSD-Schema geladen aus: %s", config.schema_pfad)
    else:
        logger.info("Kein XSD-Schema – nur Syntax-Validierung.")

    # Modell einmalig laden
    try:
        generator = KIGenerator(config)
    except Exception as exc:
        logger.error("Modell konnte nicht geladen werden: %s", exc)
        return 1

    fehler_gesamt = 0

    for excel_pfad in alle_dateien:
        logger.info("── Verarbeite: %s", excel_pfad.name)

        # 1. Excel einlesen
        try:
            excel_data = parse_excel(str(excel_pfad))
            logger.info("  Excel: '%s' – %d Zeilen", excel_data.formularname, len(excel_data.zeilen))
        except ExcelParseError as exc:
            logger.error("  Excel-Fehler: %s", exc)
            fehler_gesamt += 1
            continue

        # 2. XML generieren (mit Retry)
        try:
            xml_roh = generator.generiere_xml(excel_data)
        except XMLGenerierungFehler as exc:
            logger.error("  Generierung fehlgeschlagen: %s", exc)
            fehler_gesamt += 1
            continue

        # 3. Pretty-Print
        try:
            xml_formatiert = pretty_print_xml(xml_roh)
        except ValueError as exc:
            logger.error("  Formatierung fehlgeschlagen: %s", exc)
            fehler_gesamt += 1
            continue

        # 4. XSD-Validierung (optional)
        if xsd_schema:
            xsd_ok, xsd_fehler = validiere_gegen_xsd(xml_formatiert, xsd_schema)
            if xsd_ok:
                logger.info("  ✓ XSD-Validierung bestanden.")
            else:
                logger.warning("  ⚠ XSD-Warnung: %s", xsd_fehler)
                print(f"  ⚠ XSD [{excel_pfad.name}]: {xsd_fehler}")

        # 5. Speichern
        ausgabe_pfad = speichere_xml(xml_formatiert, str(excel_pfad), config.ausgabe_pfad)
        logger.info("  ✓ XML gespeichert: %s", ausgabe_pfad)
        print(f"  ✓ {excel_pfad.name} → {ausgabe_pfad}")

    print(f"\n{'='*60}")
    if fehler_gesamt == 0:
        print(f"  Alle {len(alle_dateien)} Datei(en) erfolgreich konvertiert.")
    else:
        print(f"  {len(alle_dateien) - fehler_gesamt}/{len(alle_dateien)} konvertiert "
              f"({fehler_gesamt} Fehler – siehe pipeline.log)")
    print(f"{'='*60}")
    return 0 if fehler_gesamt == 0 else 2


# ────────────────────────────────────────────────────────────────
# Einstiegspunkt
# ────────────────────────────────────────────────────────────────

def main() -> int:
    parser = _erstelle_parser()
    args = parser.parse_args()

    # Konfiguration laden
    try:
        config = lade_config(args.config)
    except (FileNotFoundError, ValueError) as exc:
        print(f"[FEHLER] Konfiguration: {exc}", file=sys.stderr)
        return 1

    # CLI-Overrides
    if args.log_level:
        config.log_level = args.log_level

    # Logging initialisieren
    setup_logger(log_level=config.log_level, log_datei=config.log_datei)
    logger.info("Pipeline gestartet – Modus: %s", args.modus)

    # Modus ausführen
    if args.modus == "jsonl":
        return _modus_jsonl(config)

    elif args.modus == "training":
        return _modus_training(config, getattr(args, "epochs", None))

    elif args.modus == "test":
        return _modus_test(config)

    elif args.modus == "konvertiere":
        return _modus_konvertiere(
            config,
            args.excel_eingabe,
            getattr(args, "ausgabe", None),
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())

