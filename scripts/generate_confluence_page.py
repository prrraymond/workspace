#!/usr/bin/env python3
"""
Product Landscape → Confluence Page Generator

Reads product data from CSV, generates a self-contained HTML visualization,
and updates a Confluence page via REST API.

Usage:
    # Generate HTML only (preview locally)
    python scripts/generate_confluence_page.py --csv data/products.csv --output preview.html

    # Generate and push to Confluence
    python scripts/generate_confluence_page.py --csv data/products.csv --publish

Environment variables (for --publish):
    CONFLUENCE_URL      Base URL (e.g. https://yourcompany.atlassian.net/wiki)
    CONFLUENCE_PAGE_ID  Page ID to update
    CONFLUENCE_USER     Email address
    CONFLUENCE_TOKEN    API token
"""

import argparse
import csv
import html
import json
import os
import sys
from collections import Counter, OrderedDict
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import base64

# ─────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────

FUNCTION_GROUPS = [
    "Marketing", "Sales", "Engineering", "Customer Success",
    "Finance", "HR & People", "Operations", "Data & Analytics",
    "Security", "IT Infrastructure", "Legal & Compliance", "Product",
]

PRODUCT_TYPES = ["Platform", "Tool", "Service", "Integration"]

FAMILY_LINES = [
    "Enterprise Suite", "Growth Cloud", "Analytics Hub", "Commerce Engine",
    "Workflow Studio", "Connect Platform", "Identity Shield", "DevOps Pipeline",
    "Insights Lab", "Talent Cloud", "Revenue Ops", "Compliance Center",
]

FUNCTION_COLORS = {
    "Marketing":          {"bg": "#DBEAFE", "text": "#1E40AF", "dot": "#3B82F6"},
    "Sales":              {"bg": "#D1FAE5", "text": "#065F46", "dot": "#10B981"},
    "Engineering":        {"bg": "#E0E7FF", "text": "#3730A3", "dot": "#6366F1"},
    "Customer Success":   {"bg": "#FEF3C7", "text": "#92400E", "dot": "#F59E0B"},
    "Finance":            {"bg": "#FEE2E2", "text": "#991B1B", "dot": "#EF4444"},
    "HR & People":        {"bg": "#FCE7F3", "text": "#9D174D", "dot": "#EC4899"},
    "Operations":         {"bg": "#EDE9FE", "text": "#5B21B6", "dot": "#8B5CF6"},
    "Data & Analytics":   {"bg": "#CFFAFE", "text": "#155E75", "dot": "#06B6D4"},
    "Security":           {"bg": "#FFEDD5", "text": "#9A3412", "dot": "#F97316"},
    "IT Infrastructure":  {"bg": "#F1F5F9", "text": "#334155", "dot": "#64748B"},
    "Legal & Compliance": {"bg": "#ECFCCB", "text": "#3F6212", "dot": "#84CC16"},
    "Product":            {"bg": "#CCFBF1", "text": "#115E59", "dot": "#14B8A6"},
}

TYPE_SHAPES = {
    "Platform":    "▪",  # rounded square
    "Tool":        "◆",  # diamond
    "Service":     "●",  # circle
    "Integration": "⊕",  # overlapping circles
}


# ─────────────────────────────────────────────────────────────
# Data loading
# ─────────────────────────────────────────────────────────────

def load_products(csv_path: str) -> list[dict]:
    """Load products from CSV file."""
    products = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            products.append({
                "name": row["name"].strip(),
                "function_group": row["function_group"].strip(),
                "product_type": row["product_type"].strip(),
                "family_line": row["family_line"].strip(),
            })
    return products


def get_products(products, family_line, product_type):
    """Filter products by family line and product type."""
    return [p for p in products if p["family_line"] == family_line and p["product_type"] == product_type]


# ─────────────────────────────────────────────────────────────
# HTML generation
# ─────────────────────────────────────────────────────────────

def generate_html(products: list[dict]) -> str:
    """Generate a self-contained HTML visualization of the product landscape."""

    total = len(products)
    family_lines_in_data = list(OrderedDict.fromkeys(
        fl for fl in FAMILY_LINES if any(p["family_line"] == fl for p in products)
    ))
    function_groups_in_data = list(OrderedDict.fromkeys(
        fg for fg in FUNCTION_GROUPS if any(p["function_group"] == fg for p in products)
    ))

    # Distribution counts
    fg_counts = Counter(p["function_group"] for p in products)
    type_counts = Counter(p["product_type"] for p in products)
    fl_counts = Counter(p["family_line"] for p in products)

    # ── Build the page ──────────────────────────────────────

    def esc(s):
        return html.escape(s)

    def badge(product):
        c = FUNCTION_COLORS.get(product["function_group"], {"bg": "#F1F5F9", "text": "#334155", "dot": "#64748B"})
        return (
            f'<span class="badge" style="background:{c["bg"]};color:{c["text"]};border:1px solid {c["dot"]}20" '
            f'title="{esc(product["name"])}\n{esc(product["function_group"])} · {esc(product["product_type"])}\n{esc(product["family_line"])}">'
            f'<span class="dot" style="background:{c["dot"]}"></span>'
            f'{esc(product["name"])}'
            f'</span>'
        )

    def distribution_bar(label, count, max_count, color):
        pct = (count / max_count * 100) if max_count > 0 else 0
        return (
            f'<div class="dist-row">'
            f'<span class="dist-label">{esc(label)}</span>'
            f'<div class="dist-track"><div class="dist-fill" style="width:{pct:.1f}%;background:{color}"></div></div>'
            f'<span class="dist-count">{count}</span>'
            f'</div>'
        )

    # ── Stats ───────────────────────────────────────────────
    n_families = len(family_lines_in_data)
    n_types = len(set(p["product_type"] for p in products))
    n_groups = len(function_groups_in_data)

    # ── Legend buttons ──────────────────────────────────────
    legend_items = []
    for fg in function_groups_in_data:
        c = FUNCTION_COLORS[fg]
        legend_items.append(
            f'<span class="legend-item">'
            f'<span class="legend-dot" style="background:{c["dot"]}"></span>'
            f'{esc(fg)}'
            f'</span>'
        )

    # ── Shape key ───────────────────────────────────────────
    shape_items = []
    for pt in PRODUCT_TYPES:
        shape_items.append(f'<span class="shape-item"><span class="shape-icon">{TYPE_SHAPES[pt]}</span> {esc(pt)}</span>')

    # ── Matrix grid ─────────────────────────────────────────
    header_cells = ['<div class="grid-corner">Family Line</div>']
    for pt in PRODUCT_TYPES:
        pt_count = type_counts.get(pt, 0)
        header_cells.append(
            f'<div class="grid-col-header">'
            f'<span class="shape-icon-lg">{TYPE_SHAPES[pt]}</span>'
            f'<div class="col-title">{esc(pt)}</div>'
            f'<div class="col-count">{pt_count} products</div>'
            f'</div>'
        )

    rows = []
    for i, fl in enumerate(family_lines_in_data):
        fl_total = fl_counts.get(fl, 0)
        bg_class = "row-even" if i % 2 == 0 else "row-odd"

        row_cells = [
            f'<div class="grid-row-label {bg_class}">'
            f'<div class="row-title">{esc(fl)}</div>'
            f'<div class="row-count">{fl_total} products</div>'
            f'</div>'
        ]

        for pt in PRODUCT_TYPES:
            cell_products = get_products(products, fl, pt)
            if cell_products:
                badges = " ".join(badge(p) for p in cell_products)
            else:
                badges = '<span class="empty-cell">&mdash;</span>'
            row_cells.append(f'<div class="grid-cell {bg_class}">{badges}</div>')

        rows.append("\n".join(row_cells))

    # ── Distribution section ────────────────────────────────
    max_fg = max(fg_counts.values()) if fg_counts else 1
    max_type = max(type_counts.values()) if type_counts else 1
    max_fl = max(fl_counts.values()) if fl_counts else 1

    fg_bars = "\n".join(
        distribution_bar(fg, fg_counts.get(fg, 0), max_fg, FUNCTION_COLORS[fg]["dot"])
        for fg in sorted(function_groups_in_data, key=lambda x: -fg_counts.get(x, 0))
    )
    type_bars = "\n".join(
        distribution_bar(pt, type_counts.get(pt, 0), max_type, "#475569")
        for pt in sorted(PRODUCT_TYPES, key=lambda x: -type_counts.get(x, 0))
    )
    fl_bars = "\n".join(
        distribution_bar(fl, fl_counts.get(fl, 0), max_fl, "#818CF8")
        for fl in sorted(family_lines_in_data, key=lambda x: -fl_counts.get(x, 0))
    )

    # ── Assemble full HTML ──────────────────────────────────
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Product Landscape</title>
<style>
/* ── Reset & Base ─────────────────────────────── */
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #fff; color: #1e293b; }}

/* ── Accent bar ───────────────────────────────── */
.accent-bar {{ height: 6px; background: linear-gradient(to right, #3B82F6, #8B5CF6, #10B981); }}

/* ── Container ────────────────────────────────── */
.container {{ max-width: 1440px; margin: 0 auto; padding: 0 24px; }}
@media (min-width: 1024px) {{ .container {{ padding: 0 40px; }} }}

/* ── Header ───────────────────────────────────── */
.header {{ border-bottom: 1px solid #e2e8f0; padding: 40px 0; }}
.header .eyebrow {{ font-size: 11px; font-weight: 600; letter-spacing: 0.15em; color: #94a3b8; text-transform: uppercase; margin-bottom: 12px; }}
.header h1 {{ font-size: 30px; font-weight: 700; color: #0f172a; letter-spacing: -0.025em; }}
.header .subtitle {{ margin-top: 8px; color: #64748b; font-size: 15px; line-height: 1.6; max-width: 640px; }}

/* Stats row */
.stats {{ display: flex; flex-wrap: wrap; gap: 16px; margin-top: 32px; }}
.stat-box {{ display: flex; align-items: center; gap: 12px; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px 20px; }}
.stat-value {{ font-size: 24px; font-weight: 700; color: #0f172a; }}
.stat-label {{ font-size: 14px; color: #64748b; }}

/* ── Legend ────────────────────────────────────── */
.legend-section {{ border-bottom: 1px solid #e2e8f0; background: #f8fafc; padding: 20px 0; }}
.legend-section .eyebrow {{ font-size: 11px; font-weight: 600; letter-spacing: 0.15em; color: #94a3b8; text-transform: uppercase; margin-bottom: 12px; }}
.legend-items {{ display: flex; flex-wrap: wrap; gap: 8px 20px; }}
.legend-item {{ display: inline-flex; align-items: center; gap: 8px; font-size: 13px; color: #334155; padding: 4px 12px; border-radius: 999px; }}
.legend-dot {{ width: 12px; height: 12px; border-radius: 3px; flex-shrink: 0; }}

/* ── Shape key ────────────────────────────────── */
.shape-section {{ border-bottom: 1px solid #f1f5f9; padding: 16px 0; }}
.shape-row {{ display: flex; align-items: center; gap: 32px; }}
.shape-row .eyebrow {{ font-size: 11px; font-weight: 600; letter-spacing: 0.15em; color: #94a3b8; text-transform: uppercase; flex-shrink: 0; }}
.shape-items {{ display: flex; flex-wrap: wrap; gap: 24px; }}
.shape-item {{ display: inline-flex; align-items: center; gap: 8px; font-size: 13px; color: #475569; }}
.shape-icon {{ font-size: 14px; color: #334155; }}
.shape-icon-lg {{ font-size: 22px; color: #334155; display: block; text-align: center; margin-bottom: 4px; }}

/* ── Matrix Grid ──────────────────────────────── */
.grid-section {{ padding: 32px 0; }}
.grid-wrapper {{ overflow-x: auto; }}
.matrix {{ display: grid; grid-template-columns: 180px repeat(4, 1fr); gap: 1px; background: #e2e8f0; border-radius: 12px; overflow: hidden; min-width: 920px; }}

.grid-corner {{ background: #fff; padding: 16px; display: flex; align-items: flex-end; font-size: 11px; font-weight: 600; letter-spacing: 0.1em; color: #94a3b8; text-transform: uppercase; }}
.grid-col-header {{ background: #fff; padding: 16px; text-align: center; }}
.col-title {{ font-size: 14px; font-weight: 600; color: #1e293b; }}
.col-count {{ font-size: 11px; color: #94a3b8; margin-top: 2px; }}

.grid-row-label {{ padding: 16px; display: flex; flex-direction: column; justify-content: flex-start; }}
.row-title {{ font-size: 13px; font-weight: 600; color: #1e293b; line-height: 1.3; }}
.row-count {{ font-size: 11px; color: #94a3b8; margin-top: 4px; }}

.grid-cell {{ padding: 12px; min-height: 72px; display: flex; flex-wrap: wrap; align-content: flex-start; gap: 6px; }}

.row-even {{ background: #fff; }}
.row-odd {{ background: #fafbfc; }}

/* ── Badges ───────────────────────────────────── */
.badge {{ display: inline-flex; align-items: center; padding: 5px 10px; border-radius: 6px; font-size: 11px; font-weight: 500; line-height: 1; white-space: nowrap; cursor: default; }}
.badge .dot {{ width: 6px; height: 6px; border-radius: 50%; margin-right: 6px; flex-shrink: 0; }}
.empty-cell {{ color: #cbd5e1; font-size: 12px; }}

/* ── Distribution ─────────────────────────────── */
.dist-section {{ border-top: 1px solid #e2e8f0; background: #f8fafc; padding: 40px 0; }}
.dist-section .eyebrow {{ font-size: 11px; font-weight: 600; letter-spacing: 0.15em; color: #94a3b8; text-transform: uppercase; margin-bottom: 24px; }}
.dist-grid {{ display: grid; grid-template-columns: 1fr; gap: 40px; }}
@media (min-width: 768px) {{ .dist-grid {{ grid-template-columns: repeat(3, 1fr); }} }}
.dist-col h3 {{ font-size: 14px; font-weight: 600; color: #334155; margin-bottom: 16px; }}
.dist-row {{ display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }}
.dist-label {{ font-size: 11px; color: #64748b; width: 120px; text-align: right; flex-shrink: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
.dist-track {{ flex: 1; height: 16px; background: #f1f5f9; border-radius: 2px; overflow: hidden; }}
.dist-fill {{ height: 100%; border-radius: 2px; }}
.dist-count {{ font-size: 11px; font-weight: 500; color: #475569; width: 20px; text-align: right; flex-shrink: 0; }}

/* ── Footer ───────────────────────────────────── */
.footer {{ border-top: 1px solid #e2e8f0; padding: 24px 0; }}
.footer p {{ font-size: 12px; color: #94a3b8; }}
</style>
</head>
<body>

<div class="accent-bar"></div>

<!-- Header -->
<header class="header">
  <div class="container">
    <p class="eyebrow">Organization Overview</p>
    <h1>Product Landscape</h1>
    <p class="subtitle">
      How our {total} products align across function groups, product types,
      and family lines &mdash; a single view of the full portfolio.
    </p>
    <div class="stats">
      <div class="stat-box"><span class="stat-value">{total}</span><span class="stat-label">Products</span></div>
      <div class="stat-box"><span class="stat-value">{n_families}</span><span class="stat-label">Family Lines</span></div>
      <div class="stat-box"><span class="stat-value">{n_types}</span><span class="stat-label">Product Types</span></div>
      <div class="stat-box"><span class="stat-value">{n_groups}</span><span class="stat-label">Function Groups</span></div>
    </div>
  </div>
</header>

<!-- Function Group Legend -->
<section class="legend-section">
  <div class="container">
    <p class="eyebrow">Function Groups</p>
    <div class="legend-items">
      {" ".join(legend_items)}
    </div>
  </div>
</section>

<!-- Shape Key -->
<section class="shape-section">
  <div class="container">
    <div class="shape-row">
      <p class="eyebrow">Product Types</p>
      <div class="shape-items">
        {" ".join(shape_items)}
      </div>
    </div>
  </div>
</section>

<!-- Matrix Grid -->
<section class="grid-section">
  <div class="container">
    <div class="grid-wrapper">
      <div class="matrix">
        {"".join(header_cells)}
        {"".join(rows)}
      </div>
    </div>
  </div>
</section>

<!-- Distribution Summary -->
<section class="dist-section">
  <div class="container">
    <p class="eyebrow">Distribution Summary</p>
    <div class="dist-grid">
      <div class="dist-col">
        <h3>By Function Group</h3>
        {fg_bars}
      </div>
      <div class="dist-col">
        <h3>By Product Type</h3>
        {type_bars}
      </div>
      <div class="dist-col">
        <h3>By Family Line</h3>
        {fl_bars}
      </div>
    </div>
  </div>
</section>

<!-- Footer -->
<footer class="footer">
  <div class="container">
    <p>Product Landscape &middot; {total} Products &middot; 3 Classification Dimensions</p>
  </div>
</footer>

</body>
</html>"""


# ─────────────────────────────────────────────────────────────
# Confluence integration
# ─────────────────────────────────────────────────────────────

def confluence_api(method: str, path: str, body: dict | None = None) -> dict:
    """Make a Confluence REST API call."""
    base_url = os.environ["CONFLUENCE_URL"].rstrip("/")
    user = os.environ["CONFLUENCE_USER"]
    token = os.environ["CONFLUENCE_TOKEN"]

    url = f"{base_url}/rest/api{path}"
    credentials = base64.b64encode(f"{user}:{token}".encode()).decode()

    headers = {
        "Authorization": f"Basic {credentials}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    data = json.dumps(body).encode("utf-8") if body else None
    req = Request(url, data=data, headers=headers, method=method)

    try:
        with urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        print(f"Confluence API error {e.code}: {error_body}", file=sys.stderr)
        raise


def get_page(page_id: str) -> dict:
    """Get current page info (needed for version number)."""
    return confluence_api("GET", f"/content/{page_id}?expand=version,body.storage")


def update_page(page_id: str, title: str, html_body: str, current_version: int) -> dict:
    """Update a Confluence page with new HTML content."""
    # Wrap in Confluence HTML macro for full rendering
    storage_body = (
        '<ac:structured-macro ac:name="html">'
        '<ac:plain-text-body><![CDATA['
        f'{html_body}'
        ']]></ac:plain-text-body>'
        '</ac:structured-macro>'
    )

    body = {
        "version": {"number": current_version + 1},
        "title": title,
        "type": "page",
        "body": {
            "storage": {
                "value": storage_body,
                "representation": "storage",
            }
        },
    }
    return confluence_api("PUT", f"/content/{page_id}", body)


def publish_to_confluence(html_content: str):
    """Publish the generated HTML to a Confluence page."""
    page_id = os.environ["CONFLUENCE_PAGE_ID"]

    print(f"Fetching current page {page_id}...")
    page = get_page(page_id)
    title = page["title"]
    current_version = page["version"]["number"]

    print(f"Updating '{title}' (v{current_version} → v{current_version + 1})...")
    result = update_page(page_id, title, html_content, current_version)
    new_version = result["version"]["number"]

    base_url = os.environ["CONFLUENCE_URL"].rstrip("/")
    page_url = f"{base_url}/pages/viewpage.action?pageId={page_id}"
    print(f"Done! Page updated to v{new_version}")
    print(f"View: {page_url}")


# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate Product Landscape for Confluence")
    parser.add_argument("--csv", required=True, help="Path to products CSV file")
    parser.add_argument("--output", help="Write HTML to file (for local preview)")
    parser.add_argument("--publish", action="store_true", help="Publish to Confluence (requires env vars)")
    args = parser.parse_args()

    # Load data
    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"Error: CSV file not found: {csv_path}", file=sys.stderr)
        sys.exit(1)

    products = load_products(str(csv_path))
    print(f"Loaded {len(products)} products from {csv_path}")

    # Generate HTML
    html_content = generate_html(products)
    print(f"Generated HTML ({len(html_content):,} bytes)")

    # Output
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(html_content, encoding="utf-8")
        print(f"Written to {output_path}")

    if args.publish:
        required_vars = ["CONFLUENCE_URL", "CONFLUENCE_PAGE_ID", "CONFLUENCE_USER", "CONFLUENCE_TOKEN"]
        missing = [v for v in required_vars if not os.environ.get(v)]
        if missing:
            print(f"Error: Missing environment variables: {', '.join(missing)}", file=sys.stderr)
            print("Set these before using --publish:", file=sys.stderr)
            for v in required_vars:
                print(f"  export {v}=...", file=sys.stderr)
            sys.exit(1)
        publish_to_confluence(html_content)

    if not args.output and not args.publish:
        print("Tip: Use --output preview.html to save locally, or --publish to push to Confluence")


if __name__ == "__main__":
    main()
