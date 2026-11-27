"""Unit tests for Product Knowledge Enricher (HTML cleaning, JSON-LD Product specs, & URL guardrails)."""

from src.knowledge_enricher import (
    extract_structured_html_knowledge,
    fetch_url_product_knowledge,
    gather_product_knowledge_context,
)


def test_extracts_json_ld_product_specs_and_clean_body():
    sample_html = """
    <html>
      <head>
        <title>TrailTop Kursi Lipat Kermit 600D | Official Website</title>
        <meta name="description" content="Kursi lipat outdoor kanvas Oxford 600D beban 150kg.">
        <script type="application/ld+json">
        {
          "@context": "https://schema.org",
          "@type": "Product",
          "name": "TrailTop Kursi Lipat Kermit",
          "material": "600D Tear-Resistant Oxford Canvas + Carbon Steel X-Frame",
          "brand": {"@type": "Brand", "name": "TrailTop"},
          "aggregateRating": {"@type": "AggregateRating", "ratingValue": "4.9", "reviewCount": "1820"},
          "additionalProperty": [
            {"@type": "PropertyValue", "name": "Beban Maksimal", "value": "150 kg"},
            {"@type": "PropertyValue", "name": "Berat Bersih", "value": "2.4 kg"}
          ]
        }
        </script>
        <script>console.log("ignore noisy js");</script>
      </head>
      <body>
        <nav>Menu Utama</nav>
        <main>
          <h1>Spesifikasi Lengkap</h1>
          <p>Dilengkapi gagang kayu beechwood halus dan kantong samping multifungsi.</p>
        </main>
      </body>
    </html>
    """
    extracted = extract_structured_html_knowledge(sample_html)
    assert "600D Tear-Resistant Oxford Canvas" in extracted
    assert "Spek Beban Maksimal: 150 kg" in extracted
    assert "Rating Publik: 4.9" in extracted
    assert "beechwood" in extracted
    assert "ignore noisy js" not in extracted


def test_invalid_url_handled_gracefully():
    txt, msg = fetch_url_product_knowledge("ftp://bad-scheme.example.com")
    assert txt == ""
    assert "tidak valid" in msg.lower()


def test_gather_context_combines_pasted_specs_without_network():
    ctx = gather_product_knowledge_context(
        product_url="",
        raw_specs_text="Bahan pipa baja 16mm anti karat, kain Oxford 600D dua lapis.",
        auto_web_search=False,
    )
    assert "Oxford 600D" in ctx.combined_text
    assert "Deskripsi/Spesifikasi Toko" in ctx.sources_used
