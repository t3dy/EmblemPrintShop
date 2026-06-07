"""
Pytest configuration for EmblemPrintShop tests.

Suppresses HuggingFace model-loading progress bars so test output
stays readable. Models are cached after first download.
"""
import os
import logging

# Silence HuggingFace Hub and tqdm progress bars during test runs
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")

logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
