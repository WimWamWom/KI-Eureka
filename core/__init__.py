"""
core – Excel-zu-XML-Pipeline mit KI-Unterstützung.

HINWEIS: Einige Importe werden verzögert geladen (lazy imports),
um Probleme mit fehlenden System-Bibliotheken (_lzma) zu vermeiden.
"""

from .config import AppConfig, lade_config
from .models import ExcelData, ConversionResult
from .excel_parser import parse_excel, ExcelParseError
from .ki_generator import KIGenerator, XMLGenerierungFehler
from .xml_validator import validiere_xml, pretty_print_xml, validiere_gegen_xsd, lade_xsd_schema
from .file_writer import speichere_xml
from .jsonl_ersteller import erstelle_jsonl

# Lazy imports für Module, die 'datasets' benötigen (wegen _lzma)
# from .trainer import trainiere_modell
# from .tester import teste_modell, Testbericht, Testergebnis

__all__ = [
    "AppConfig", "lade_config",
    "ExcelData", "ConversionResult",
    "parse_excel", "ExcelParseError",
    "KIGenerator", "XMLGenerierungFehler",
    "validiere_xml", "validiere_gegen_xsd", "lade_xsd_schema", "pretty_print_xml",
    "speichere_xml",
    "erstelle_jsonl",
    "trainiere_modell",
    "teste_modell", "Testbericht", "Testergebnis",
]


def __getattr__(name):
    """Lazy loading für Module mit schweren Abhängigkeiten."""
    if name == "trainiere_modell":
        from .trainer import trainiere_modell
        return trainiere_modell
    elif name == "teste_modell":
        from .tester import teste_modell
        return teste_modell
    elif name == "Testbericht":
        from .tester import Testbericht
        return Testbericht
    elif name == "Testergebnis":
        from .tester import Testergebnis
        return Testergebnis
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


