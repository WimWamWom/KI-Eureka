"""
Fine-Tuning des Mistral-7B-Modells mit QLoRA (Supervised Fine-Tuning).

Liest JSONL-Trainingsdaten und speichert den LoRA-Adapter nach modell/modell_output/.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

import torch
from datasets import Dataset
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    PreTrainedTokenizerBase,
    TrainingArguments,
)
from trl import SFTTrainer

from .config import AppConfig

logger = logging.getLogger(__name__)


def _lade_jsonl(pfad: Path) -> list[dict]:
    """Liest JSONL-Datei und gibt Liste von Dicts zurück."""
    if not pfad.exists():
        raise FileNotFoundError(f"JSONL-Datei nicht gefunden: {pfad}")

    eintraege = []
    with open(pfad, encoding="utf-8") as f:
        for zeile in f:
            zeile = zeile.strip()
            if zeile:
                try:
                    eintraege.append(json.loads(zeile))
                except json.JSONDecodeError as exc:
                    logger.warning("Zeile übersprungen (JSON-Fehler): %s", exc)

    logger.info("%d Trainingsbeispiele geladen.", len(eintraege))
    return eintraege


def _formatiere_fuer_mistral(eintraege: list[dict]) -> list[dict]:
    """Formatiert Einträge im Mistral-Instruct-Format: [INST] prompt [/INST] completion."""
    return [
        {
            "text": (
                f"[INST] Konvertiere die folgenden JSON-Formulardaten in ein "
                f"gültiges SpreadsheetML-XML-Dokument.\n"
                f"Gib ausschließlich das XML zurück, ohne Erklärungen.\n\n"
                f"{e.get('prompt', '')} [/INST] {e.get('completion', '')}"
            )
        }
        for e in eintraege
    ]


def trainiere_modell(config: AppConfig) -> Path:
    """
    Führt das Supervised Fine-Tuning durch.

    Returns:
        Pfad zum gespeicherten Modell-Output-Ordner.
    """
    basis_ordner = Path(__file__).resolve().parent.parent

    jsonl_pfad = Path(config.jsonl_pfad).resolve()
    ausgabe_ordner = basis_ordner / "modell" / "modell_output"
    checkpoint_ordner = basis_ordner / "modell" / "checkpoints"
    logs_ordner = basis_ordner / "modell" / "logs"

    for ordner in (ausgabe_ordner, checkpoint_ordner, logs_ordner):
        ordner.mkdir(parents=True, exist_ok=True)

    # --- Daten laden ---
    rohdaten = _lade_jsonl(jsonl_pfad)
    formatiert = _formatiere_fuer_mistral(rohdaten)
    dataset = Dataset.from_list(formatiert)
    logger.info("Dataset: %d Beispiele", len(dataset))

    # --- Quantisierung ---
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    # --- Modell und Tokenizer ---
    logger.info("Lade Basis-Modell: %s", config.basis_modell)
    tokenizer: PreTrainedTokenizerBase = AutoTokenizer.from_pretrained(
        config.basis_modell, trust_remote_code=True
    )
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    modell = AutoModelForCausalLM.from_pretrained(
        config.basis_modell,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )
    modell.config.use_cache = False
    modell.config.pretraining_tp = 1

    # --- LoRA konfigurieren ---
    lora_config = LoraConfig(
        lora_alpha=config.lora_alpha,
        lora_dropout=config.lora_dropout,
        r=config.lora_r,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"],
    )
    modell = prepare_model_for_kbit_training(modell)
    modell = get_peft_model(modell, lora_config)

    trainierbar = sum(p.numel() for p in modell.parameters() if p.requires_grad)
    gesamt = sum(p.numel() for p in modell.parameters())
    logger.info("Trainierbare Parameter: %s / %s (%.2f%%)",
                f"{trainierbar:,}", f"{gesamt:,}", 100 * trainierbar / gesamt)

    # --- Training ---
    training_args = TrainingArguments(
        output_dir=str(checkpoint_ordner),
        num_train_epochs=config.num_train_epochs,
        per_device_train_batch_size=config.batch_size,
        gradient_accumulation_steps=config.gradient_accumulation_steps,
        gradient_checkpointing=True,
        optim="paged_adamw_32bit",
        save_steps=100,
        logging_steps=10,
        learning_rate=config.learning_rate,
        weight_decay=0.001,
        fp16=True,
        bf16=False,
        max_grad_norm=0.3,
        warmup_steps=100,
        group_by_length=True,
        lr_scheduler_type="cosine",
        report_to="none",
        save_total_limit=3,
    )

    trainer = SFTTrainer(
        model=modell,
        train_dataset=dataset,
        tokenizer=tokenizer,  # type: ignore[arg-type]
        args=training_args,
        dataset_text_field="text",  # type: ignore[call-arg]
        max_seq_length=config.max_seq_length,  # type: ignore[call-arg]
        packing=False,  # type: ignore[call-arg]
    )

    logger.info("Training gestartet …")
    start = datetime.now()
    trainer.train()
    dauer = datetime.now() - start
    logger.info("Training abgeschlossen. Dauer: %s", dauer)

    # --- Modell speichern ---
    trainer.model.save_pretrained(str(ausgabe_ordner))
    tokenizer.save_pretrained(str(ausgabe_ordner))
    logger.info("Modell gespeichert: %s", ausgabe_ordner)

    return ausgabe_ordner




