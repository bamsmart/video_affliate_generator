"""Product Knowledge Enricher: extracts specs from brand/review URLs, JSON-LD, web snippets, & pasted specs."""

from __future__ import annotations

import json
import re
import urllib.parse
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Any

import certifi
import requests

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


@dataclass
class KnowledgeContext:
    combined_text: str = ""
    sources_used: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class _CleanHTMLParser(HTMLParser):
    """Lightweight stdlib HTML parser extracting title, meta descriptions, JSON-LD, and body text."""

    _SKIP_TAGS = {"script", "style", "noscript", "svg", "nav", "footer", "iframe"}

    def __init__(self) -> None:
        super().__init__()
        self._skip_depth = 0
        self._in_title = False
        self._in_json_ld = False
        self.title_parts: list[str] = []
        self.meta_descriptions: list[str] = []
        self.json_ld_blocks: list[str] = []
        self._current_ld: list[str] = []
        self.text_chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        t = tag.lower()
        attr_map = {k.lower(): (v or "") for k, v in attrs}

        if t == "script" and "ld+json" in attr_map.get("type", "").lower():
            self._in_json_ld = True
            self._current_ld = []
            return

        if t in self._SKIP_TAGS:
            self._skip_depth += 1
            return

        if t == "title":
            self._in_title = True
        elif t == "meta":
            name = (attr_map.get("name") or attr_map.get("property") or "").lower()
            content = attr_map.get("content", "").strip()
            if content and name in ("description", "og:description", "og:title", "twitter:description"):
                self.meta_descriptions.append(content)

    def handle_endtag(self, tag: str) -> None:
        t = tag.lower()
        if t == "script" and self._in_json_ld:
            self._in_json_ld = False
            raw_ld = "".join(self._current_ld).strip()
            if raw_ld:
                self.json_ld_blocks.append(raw_ld)
            self._current_ld = []
            return

        if t in self._SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1
        elif t == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_json_ld:
            self._current_ld.append(data)
            return
        if self._skip_depth > 0:
            return
        cleaned = re.sub(r"\s+", " ", data).strip()
        if not cleaned:
            return
        if self._in_title:
            self.title_parts.append(cleaned)
        else:
            self.text_chunks.append(cleaned)


def _walk_json_ld_products(obj: Any, out: list[str]) -> None:
    if isinstance(obj, list):
        for item in obj:
            _walk_json_ld_products(item, out)
        return
    if not isinstance(obj, dict):
        return

    ld_type = str(obj.get("@type", "")).lower()
    if "product" in ld_type:
        for key, label in (
            ("name", "Nama Produk"),
            ("description", "Deskripsi Resmi"),
            ("material", "Material"),
            ("category", "Kategori"),
            ("sku", "SKU"),
        ):
            val = obj.get(key)
            if isinstance(val, str) and val.strip():
                out.append(f"{label}: {val.strip()}")

        brand = obj.get("brand")
        if isinstance(brand, dict) and brand.get("name"):
            out.append(f"Brand: {brand['name']}")
        elif isinstance(brand, str) and brand.strip():
            out.append(f"Brand: {brand.strip()}")

        rating = obj.get("aggregateRating")
        if isinstance(rating, dict) and rating.get("ratingValue"):
            rc = rating.get("reviewCount") or rating.get("ratingCount") or ""
            out.append(f"Rating Publik: {rating['ratingValue']} ({rc} ulasan)".strip())

        add_props = obj.get("additionalProperty")
        if isinstance(add_props, list):
            for prop in add_props[:12]:
                if isinstance(prop, dict) and prop.get("name") and prop.get("value"):
                    out.append(f"Spek {prop['name']}: {prop['value']}")

    for val in obj.values():
        if isinstance(val, (dict, list)):
            _walk_json_ld_products(val, out)


def extract_structured_html_knowledge(html_text: str, max_chars: int = 3800) -> str:
    """Extract clean product facts (title, meta, JSON-LD Product specs, and body paragraphs) from HTML."""
    parser = _CleanHTMLParser()
    parser.feed(html_text or "")

    sections: list[str] = []
    if parser.title_parts:
        sections.append("Judul Halaman: " + " ".join(parser.title_parts))

    unique_metas = list(dict.fromkeys(parser.meta_descriptions))
    if unique_metas:
        sections.append("Ringkasan Meta: " + " | ".join(unique_metas[:3]))

    ld_facts: list[str] = []
    for raw_ld in parser.json_ld_blocks:
        try:
            parsed = json.loads(raw_ld)
            _walk_json_ld_products(parsed, ld_facts)
        except Exception:
            continue
    if ld_facts:
        sections.append("Data Produk Terstruktur (JSON-LD):\n- " + "\n- ".join(dict.fromkeys(ld_facts)))

    body_text = " ".join(parser.text_chunks)
    body_text = re.sub(r"\s+", " ", body_text).strip()
    if body_text:
        sections.append("Isi Halaman:\n" + body_text[:max_chars])

    combined = "\n\n".join(sections).strip()
    return combined[: max_chars + 1200]


def fetch_url_product_knowledge(url: str, timeout_sec: float = 8.0) -> tuple[str, str]:
    """Fetch public product/brand webpage knowledge safely without bypassing anti-bot gates.

    Returns `(extracted_text, status_message)`.
    """
    clean_url = url.strip()
    if not clean_url:
        return "", ""

    parsed = urllib.parse.urlparse(clean_url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return "", "Format URL tidak valid (gunakan awalan https://)."

    try:
        resp = requests.get(
            clean_url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8",
            },
            timeout=timeout_sec,
            verify=certifi.where(),
        )
        if resp.status_code in (401, 403, 429):
            return (
                "",
                f"Halaman ({parsed.netloc}) membatasi akses bot otomatis ({resp.status_code}). "
                "Tips: Anda bisa copy-paste teks deskripsi produk langsung ke kolom Spesifikasi Toko.",
            )
        if resp.status_code >= 400:
            return "", f"Gagal membaca URL ({resp.status_code})."

        extracted = extract_structured_html_knowledge(resp.text)
        if len(extracted) < 80:
            return (
                "",
                f"Halaman ({parsed.netloc}) menggunakan proteksi login/JS penuh sehingga teks spek tidak terbuka publik. "
                "Gunakan copy-paste deskripsi toko untuk detail tambahan.",
            )
        return extracted, f"Berhasil mengekstrak pengetahuan produk dari {parsed.netloc}"
    except Exception:
        return "", f"Tidak dapat menjangkau {parsed.netloc} (timeout/koneksi); lanjut dengan analisis AI."


def search_public_web_snippets(query: str, timeout_sec: float = 5.0) -> str:
    """Fetch lightweight public product reference snippets when a search query is available."""
    q = query.strip()
    if len(q) < 4:
        return ""
    try:
        resp = requests.get(
            "https://html.duckduckgo.com/html/",
            params={"q": f"{q} spesifikasi review kelebihan"},
            headers={"User-Agent": USER_AGENT},
            timeout=timeout_sec,
            verify=certifi.where(),
        )
        if resp.status_code != 200:
            return ""
        # Extract snippet text cleanly without heavy dependencies
        snippets = re.findall(
            r'class="result__snippet"[^>]*>(.*?)</a>|class="result__snippet"[^>]*>(.*?)</td>',
            resp.text,
            flags=re.IGNORECASE | re.DOTALL,
        )
        cleaned_list: list[str] = []
        for pair in snippets[:5]:
            raw = pair[0] or pair[1]
            txt = re.sub(r"<[^>]+>", " ", raw)
            txt = re.sub(r"\s+", " ", txt).strip()
            if txt and len(txt) > 25:
                cleaned_list.append(f"- {txt}")
        return "\n".join(cleaned_list)
    except Exception:
        return ""


def gather_product_knowledge_context(
    product_url: str = "",
    raw_specs_text: str = "",
    auto_web_search: bool = True,
    search_hint: str = "",
) -> KnowledgeContext:
    """Combine URL extraction, pasted store specifications, and optional public web snippets."""
    blocks: list[str] = []
    sources: list[str] = []
    warnings: list[str] = []

    if raw_specs_text and raw_specs_text.strip():
        blocks.append("=== SPESIFIKASI / DESKRIPSI PRODUK DARI PENGGUNA ===\n" + raw_specs_text.strip()[:4000])
        sources.append("Deskripsi/Spesifikasi Toko")

    if product_url and product_url.strip():
        url_text, msg = fetch_url_product_knowledge(product_url)
        if url_text:
            blocks.append(f"=== DATA DARI WEBSITE ({product_url.strip()}) ===\n{url_text}")
            sources.append(f"Website ({urllib.parse.urlparse(product_url.strip()).netloc})")
        elif msg:
            warnings.append(msg)

    query_seed = search_hint.strip()
    if not query_seed and product_url.strip():
        # Derive readable product keywords from URL slug even if marketplace HTML is login-gated!
        path_slug = urllib.parse.unquote(urllib.parse.urlparse(product_url.strip()).path)
        slug_words = re.sub(r"[-_/?.=0-9]+", " ", path_slug).strip()
        if len(slug_words) >= 6:
            query_seed = slug_words[:80]

    if auto_web_search and query_seed:
        web_snips = search_public_web_snippets(query_seed)
        if web_snips:
            blocks.append(f"=== REFERENSI REVIEW & SPEK PUBLIK WEB ({query_seed}) ===\n{web_snips}")
            sources.append("Riset Web Publik")

    return KnowledgeContext(
        combined_text="\n\n".join(blocks).strip(),
        sources_used=sources,
        warnings=warnings,
    )
