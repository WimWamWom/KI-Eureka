"""XML-Syntaxvalidierung, XSD-Schema-Validierung und Pretty-Printing mit lxml."""

from __future__ import annotations

from pathlib import Path

from lxml import etree


def validiere_xml(xml_string: str) -> tuple[bool, str | None]:
    """
    Prüft ob der übergebene String wohlgeformtes XML ist.

    Returns:
        (True, None)           bei gültigem XML
        (False, Fehlermeldung) bei ungültigem XML
    """
    if not xml_string or not xml_string.strip():
        return False, "Leere XML-Ausgabe."

    xml_bytes = xml_string.encode("utf-8") if isinstance(xml_string, str) else xml_string

    try:
        etree.fromstring(xml_bytes)
        return True, None
    except etree.XMLSyntaxError as exc:
        return False, str(exc)


def lade_xsd_schema(schema_ordner: str) -> etree.XMLSchema | None:
    """
    Sucht im angegebenen Ordner nach der ersten *.xsd-Datei und lädt sie.
    Gibt None zurück wenn kein Schema gefunden wird (kein Fehler).

    Args:
        schema_ordner: Pfad zum Ordner mit XSD-Dateien (z.B. daten/schema/)
    """
    ordner = Path(schema_ordner).resolve()
    if not ordner.exists():
        return None

    xsd_dateien = list(ordner.glob("*.xsd"))
    if not xsd_dateien:
        return None

    xsd_pfad = xsd_dateien[0]
    try:
        schema_doc = etree.parse(str(xsd_pfad))
        schema = etree.XMLSchema(schema_doc)
        return schema
    except Exception:
        return None


def validiere_gegen_xsd(
    xml_string: str, schema: etree.XMLSchema
) -> tuple[bool, str | None]:
    """
    Validiert das XML gegen ein geladenes XSD-Schema.

    Returns:
        (True, None)           bei gültigem XML
        (False, Fehlermeldung) bei Schema-Verletzung
    """
    xml_bytes = xml_string.encode("utf-8") if isinstance(xml_string, str) else xml_string

    try:
        doc = etree.fromstring(xml_bytes)
        schema.assertValid(etree.ElementTree(doc))
        return True, None
    except etree.DocumentInvalid as exc:
        return False, str(exc)
    except etree.XMLSyntaxError as exc:
        return False, str(exc)


def pretty_print_xml(xml_string: str) -> str:
    """
    Formatiert XML mit Einrückung, UTF-8-Deklaration und Zeilenumbrüchen.

    Raises:
        ValueError: Wenn das XML nicht geparst werden kann.
    """
    xml_bytes = xml_string.encode("utf-8") if isinstance(xml_string, str) else xml_string

    try:
        root = etree.fromstring(xml_bytes)
    except etree.XMLSyntaxError as exc:
        raise ValueError(f"XML kann nicht formatiert werden: {exc}") from exc

    baum = etree.ElementTree(root)
    ergebnis: bytes = etree.tostring(
        baum,
        xml_declaration=True,
        encoding="UTF-8",
        pretty_print=True,  # type: ignore[call-arg]
    )
    return ergebnis.decode("utf-8")
