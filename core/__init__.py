"""
core – Excel-zu-XML-Pipeline mit KI-Unterstützung.
"""

from .config import AppConfig, lade_config
from .models import ExcelData, ConversionResult
from .excel_parser import parse_excel, ExcelParseError
from .ki_generator import KIGenerator, XMLGenerierungFehler
from .xml_validator import validiere_xml, pretty_print_xml
from .file_writer import speichere_xml
from .jsonl_ersteller import erstelle_jsonl
from .trainer import trainiere_modell
from .tester import teste_modell, Testbericht, Testergebnis

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

