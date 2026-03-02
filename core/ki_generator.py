"""
KI-Generator: Lädt das fine-getunete Mistral-7B-Modell und generiert XML aus ExcelData.

Das Modell wird einmalig beim Initialisieren geladen und bleibt im Speicher.
Bei fehlendem LoRA-Adapter wird automatisch auf das Basis-Modell zurückgefallen.
"""

from __future__ import annotations

import logging
import re

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

try:
    from peft import PeftModel
    _PEFT_VERFUEGBAR = True
except ImportError:
    PeftModel = None  # type: ignore[assignment,misc]
    _PEFT_VERFUEGBAR = False

from .config import AppConfig
from .models import ExcelData
from .xml_validator import validiere_xml

logger = logging.getLogger(__name__)


class XMLGenerierungFehler(Exception):
    """Wird geworfen, wenn nach allen Retries kein gültiges XML erzeugt wurde."""


_PROMPT_TEMPLATE = (
    "[INST] Konvertiere die folgenden JSON-Formulardaten in ein gültiges "
    "SpreadsheetML-XML-Dokument.\n"
    "Gib ausschließlich das XML zurück, ohne Erklärungen oder Markdown-Blöcke.\n\n"
    "{json_daten} [/INST]"
)


class KIGenerator:
    """Verwaltet das Mistral-7B-Modell und führt die JSON→XML-Generierung durch."""

    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._modell = None
        self._tokenizer = None
        self._lade_modell()

    def _erstelle_quantisierungs_config(self) -> BitsAndBytesConfig:
        return BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )

    def _lade_modell(self) -> None:
        """Lädt Basis-Modell und – falls vorhanden – den LoRA-Adapter."""
        logger.info("Lade Basis-Modell: %s", self._config.basis_modell)
        bnb_config = self._erstelle_quantisierungs_config()

        basis = AutoModelForCausalLM.from_pretrained(
            self._config.basis_modell,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True,
        )
        basis.config.use_cache = False

        modell_pfad = self._config.modell_pfad_absolut

        if _PEFT_VERFUEGBAR and modell_pfad.exists():
            logger.info("Lade LoRA-Adapter: %s", modell_pfad)
            self._modell = PeftModel.from_pretrained(basis, str(modell_pfad))
            self._tokenizer = AutoTokenizer.from_pretrained(str(modell_pfad))
            logger.info("Fine-getuntes Modell geladen.")
        else:
            if not modell_pfad.exists():
                logger.warning(
                    "LoRA-Adapter nicht gefunden (%s). Fallback auf Basis-Modell – "
                    "Qualität kann abweichen.",
                    modell_pfad,
                )
            self._modell = basis
            self._tokenizer = AutoTokenizer.from_pretrained(
                self._config.basis_modell, trust_remote_code=True
            )
            logger.info("Basis-Modell geladen (kein Fine-Tuning).")

        if self._tokenizer is not None:
            self._tokenizer.pad_token = self._tokenizer.eos_token

    def generiere_xml(self, excel_data: ExcelData) -> str:
        """
        Generiert SpreadsheetML-XML aus dem ExcelData-Objekt.

        Raises:
            XMLGenerierungFehler: Wenn nach allen Retries kein gültiges XML vorliegt.
        """
        prompt = _PROMPT_TEMPLATE.format(json_daten=excel_data.zu_json_string())
        return self._generiere_mit_retry(prompt)

    def _generiere_mit_retry(self, prompt: str) -> str:
        letzter_fehler = "Unbekannter Fehler"

        for versuch in range(1, self._config.retries + 1):
            logger.info("Generierungsversuch %d / %d …", versuch, self._config.retries)

            roh = self._inferenz(prompt)
            bereinigt = self._extrahiere_xml(roh)
            gueltig, fehler = validiere_xml(bereinigt)

            if gueltig:
                logger.info("Gültiges XML nach %d Versuch(en).", versuch)
                return bereinigt

            letzter_fehler = fehler or "Unbekannter XML-Fehler"
            logger.warning("Versuch %d – Ungültiges XML: %s", versuch, letzter_fehler)

        raise XMLGenerierungFehler(
            f"Nach {self._config.retries} Versuchen kein gültiges XML erzeugt. "
            f"Letzter Fehler: {letzter_fehler}"
        )

    def _inferenz(self, prompt: str) -> str:
        """Führt einen einzelnen Modell-Forward-Pass durch."""
        inputs = self._tokenizer(prompt, return_tensors="pt").to(self._modell.device)

        token_laenge = inputs["input_ids"].shape[1]
        max_laenge = self._config.max_seq_length
        if token_laenge > max_laenge:
            logger.error(
                "Prompt (%d Tokens) überschreitet max_seq_length (%d). "
                "Ergebnis wird wahrscheinlich fehlerhaft.",
                token_laenge, max_laenge,
            )
        elif token_laenge > max_laenge * 0.7:
            logger.warning(
                "Prompt (%d Tokens) erreicht %.0f%% der max_seq_length (%d).",
                token_laenge, 100 * token_laenge / max_laenge, max_laenge,
            )

        with torch.no_grad():
            outputs = self._modell.generate(
                **inputs,
                max_new_tokens=self._config.max_new_tokens,
                temperature=self._config.temperature,
                top_p=self._config.top_p,
                do_sample=True,
                pad_token_id=self._tokenizer.eos_token_id,
                eos_token_id=self._tokenizer.eos_token_id,
            )

        vollstaendig = self._tokenizer.decode(outputs[0], skip_special_tokens=True)

        if "[/INST]" in vollstaendig:
            return vollstaendig.split("[/INST]", 1)[-1].strip()
        return vollstaendig.strip()

    @staticmethod
    def _extrahiere_xml(text: str) -> str:
        """Extrahiert XML aus der Modellausgabe; entfernt Markdown-Blöcke."""
        markdown = re.search(r"```(?:xml)?\s*([\s\S]+?)```", text, re.IGNORECASE)
        if markdown:
            return markdown.group(1).strip()

        xml_start = text.find("<?xml")
        if xml_start == -1:
            xml_start = text.find("<")

        if xml_start != -1:
            return text[xml_start:].strip()

        return text.strip()

