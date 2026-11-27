"""Helper CLI to convert local .env into Streamlit Cloud Secrets TOML and copy to clipboard."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from dotenv import dotenv_values

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.config import format_env_as_streamlit_toml  # noqa: E402


def _mask(value: str) -> str:
    val = (value or "").strip()
    if not val:
        return "(kosong)"
    if len(val) <= 8:
        return "****"
    return f"{val[:6]}...{val[-4:]}"


def main() -> int:
    env_path = REPO_ROOT / ".env"
    if not env_path.is_file():
        print("File .env belum ditemukan di folder proyek.")
        print("Buat kunci gratis di:")
        print("  - Gemini API Key     : https://aistudio.google.com/apikey")
        print("  - OpenRouter API Key : https://openrouter.ai/keys")
        return 1

    raw_values = {k: (v or "") for k, v in dotenv_values(env_path).items() if k}
    toml_payload = format_env_as_streamlit_toml(raw_values)

    copied = False
    try:
        subprocess.run(["pbcopy"], input=toml_payload.encode("utf-8"), check=True)
        copied = True
    except Exception:
        copied = False

    print("=== Ringkasan Kunci dari .env Lokal ===")
    for k in ("GEMINI_API_KEY", "GEMINI_MODEL", "OPENROUTER_API_KEY", "APP_PIN"):
        if k in raw_values and raw_values[k]:
            shown = raw_values[k] if k == "GEMINI_MODEL" else _mask(raw_values[k])
            print(f"  {k:20s}: {shown}")

    if copied:
        print("\nBERHASIL DISALIN KE CLIPBOARD MAC ANDA!")
        print("Langkah selanjutnya (cukup 1x selamanya):")
        print("  1. Buka https://share.streamlit.io")
        print("  2. Klik titik tiga (⋮) di samping aplikasi Anda -> Settings -> Secrets")
        print("  3. Tekan Cmd + V (Paste), lalu klik Save.")
    else:
        print("\nSalin blok TOML berikut ke Streamlit Cloud -> Settings -> Secrets:\n")
        print(toml_payload)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
