#!/usr/bin/env python3
"""
Product Landscape → Confluence Page Generator

Generates a product landscape visualization designed for Confluence pages
using Bob Swift HTML macro + CSS macro.

Output modes:
  --output FILE          Standalone HTML for local browser preview
  --confluence-html FILE HTML body for the Bob Swift HTML macro
  --confluence-css FILE  CSS stylesheet for the Confluence CSS macro
  --publish              Push to Confluence via REST API (wraps in macros)

The generated HTML + CSS renders a rich visual matrix of products organized
by family line (rows) × product type (columns), color-coded by function group,
with distribution bar charts.

Usage:
    # Preview in browser
    python scripts/generate_confluence_page.py --csv data/products.csv --output preview.html

    # Generate files to paste into Confluence macros
    python scripts/generate_confluence_page.py --csv data/products.csv \\
        --confluence-html body.html --confluence-css styles.css

    # Publish directly to Confluence
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
    "Marketing":          {"bg": "#DBEAFE", "text": "#1E40AF", "border": "#93C5FD", "dot": "#3B82F6"},
    "Sales":              {"bg": "#D1FAE5", "text": "#065F46", "border": "#6EE7B7", "dot": "#10B981"},
    "Engineering":        {"bg": "#E0E7FF", "text": "#3730A3", "border": "#A5B4FC", "dot": "#6366F1"},
    "Customer Success":   {"bg": "#FEF3C7", "text": "#92400E", "border": "#FCD34D", "dot": "#F59E0B"},
    "Finance":            {"bg": "#FEE2E2", "text": "#991B1B", "border": "#FCA5A5", "dot": "#EF4444"},
    "HR & People":        {"bg": "#FCE7F3", "text": "#9D174D", "border": "#F9A8D4", "dot": "#EC4899"},
    "Operations":         {"bg": "#EDE9FE", "text": "#5B21B6", "border": "#C4B5FD", "dot": "#8B5CF6"},
    "Data & Analytics":   {"bg": "#CFFAFE", "text": "#155E75", "border": "#67E8F9", "dot": "#06B6D4"},
    "Security":           {"bg": "#FFEDD5", "text": "#9A3412", "border": "#FDBA74", "dot": "#F97316"},
    "IT Infrastructure":  {"bg": "#F1F5F9", "text": "#334155", "border": "#CBD5E1", "dot": "#64748B"},
    "Legal & Compliance": {"bg": "#ECFCCB", "text": "#3F6212", "border": "#BEF264", "dot": "#84CC16"},
    "Product":            {"bg": "#CCFBF1", "text": "#115E59", "border": "#5EEAD4", "dot": "#14B8A6"},
}

TYPE_SHAPES = {
    "Platform":    ("&#9632;", "▪"),   # ■ filled square
    "Tool":        ("&#9670;", "◆"),   # ◆ diamond
    "Service":     ("&#9679;", "●"),   # ● circle
    "Integration": ("&#10753;", "⊕"),  # ⊕ circled plus
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


def slug(s: str) -> str:
    """Convert a string to a CSS class-safe slug."""
    return s.lower().replace(" & ", "-").replace(" ", "-").replace("/", "-")


# ─────────────────────────────────────────────────────────────
# CSS generation (for the Confluence CSS macro)
# ─────────────────────────────────────────────────────────────

def generate_css() -> str:
    """Generate the CSS stylesheet for the product landscape."""

    # Function group badge colors
    fg_rules = []
    for fg, c in FUNCTION_COLORS.items():
        cls = slug(fg)
        fg_rules.append(
            f".pl-badge.fg-{cls} {{\n"
            f"  background: {c['bg']};\n"
            f"  color: {c['text']};\n"
            f"  border: 1px solid {c['border']};\n"
            f"}}\n"
            f".pl-badge.fg-{cls} .pl-dot {{\n"
            f"  background: {c['dot']};\n"
            f"}}\n"
            f".pl-legend-dot.fg-{cls} {{\n"
            f"  background: {c['dot']};\n"
            f"}}"
        )

    return f"""\
/* ═══════════════════════════════════════════════════════════
   Product Landscape – Confluence CSS Macro Stylesheet
   Paste this into a CSS macro on the same Confluence page
   ═══════════════════════════════════════════════════════════ */

/* ── Reset scoped to .pl ─────────────────────────────── */
.pl * {{ margin: 0; padding: 0; box-sizing: border-box; }}
.pl {{
  max-width: 1440px;
  margin: 0 auto;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  color: #1e293b;
  line-height: 1.5;
}}

/* ── Accent bar ──────────────────────────────────────── */
.pl-accent {{
  height: 6px;
  background: linear-gradient(to right, #3B82F6, #8B5CF6, #10B981);
  border-radius: 4px 4px 0 0;
}}

/* ── Header ──────────────────────────────────────────── */
.pl-header {{
  padding: 36px 0 28px 0;
  border-bottom: 1px solid #e2e8f0;
}}
.pl-eyebrow {{
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.15em;
  color: #94a3b8;
  text-transform: uppercase;
  margin-bottom: 10px;
}}
.pl-header h1 {{
  font-size: 30px;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
  margin-bottom: 8px;
}}
.pl-subtitle {{
  color: #64748b;
  font-size: 14px;
  line-height: 1.6;
  max-width: 640px;
  margin-bottom: 28px;
}}

/* ── Stats row ───────────────────────────────────────── */
.pl-stats {{
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
}}
.pl-stat {{
  display: flex;
  align-items: center;
  gap: 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 10px 22px;
}}
.pl-stat-val {{
  font-size: 24px;
  font-weight: 700;
  color: #0f172a;
}}
.pl-stat-lbl {{
  font-size: 13px;
  color: #64748b;
}}

/* ── Legend ───────────────────────────────────────────── */
.pl-legend {{
  background: #f8fafc;
  padding: 20px 24px;
  border-radius: 8px;
  margin: 16px 0;
}}
.pl-legend-items {{
  display: flex;
  flex-wrap: wrap;
  gap: 6px 16px;
  margin-top: 10px;
}}
.pl-legend-chip {{
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 5px 14px;
  border-radius: 999px;
  font-size: 12px;
  color: #334155;
  background: #fff;
  border: 1px solid #e2e8f0;
}}
.pl-legend-dot {{
  width: 11px;
  height: 11px;
  border-radius: 3px;
  flex-shrink: 0;
}}

/* ── Shape key ───────────────────────────────────────── */
.pl-shapes {{
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 0 20px 0;
  flex-wrap: wrap;
}}
.pl-shapes .pl-eyebrow {{
  margin-bottom: 0;
  margin-right: 8px;
}}
.pl-shape-item {{
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #475569;
  margin-right: 20px;
}}
.pl-shape-icon {{
  font-size: 15px;
  color: #334155;
}}

/* ── Matrix table ────────────────────────────────────── */
.pl-matrix-wrap {{
  overflow-x: auto;
  padding-bottom: 16px;
}}
.pl-matrix {{
  width: 100%;
  border-collapse: collapse;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  overflow: hidden;
  min-width: 920px;
}}
.pl-matrix thead th {{
  background: #fff;
  padding: 14px 12px;
  border-bottom: 2px solid #e2e8f0;
  vertical-align: bottom;
  text-align: center;
}}
.pl-matrix thead th:first-child {{
  text-align: left;
  width: 175px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.1em;
  color: #94a3b8;
  text-transform: uppercase;
}}
.pl-col-icon {{
  font-size: 22px;
  color: #334155;
  display: block;
  margin-bottom: 4px;
}}
.pl-col-title {{
  font-size: 13px;
  font-weight: 600;
  color: #1e293b;
}}
.pl-col-count {{
  font-size: 11px;
  color: #94a3b8;
}}

.pl-matrix tbody td {{
  padding: 12px;
  border-bottom: 1px solid #f1f5f9;
  vertical-align: top;
}}
.pl-matrix tbody td:first-child {{
  padding: 14px 16px;
}}
.pl-matrix tbody tr:nth-child(even) td {{
  background: #fff;
}}
.pl-matrix tbody tr:nth-child(odd) td {{
  background: #fafbfc;
}}
.pl-row-title {{
  font-size: 13px;
  font-weight: 600;
  color: #1e293b;
  display: block;
  line-height: 1.3;
}}
.pl-row-count {{
  font-size: 11px;
  color: #94a3b8;
}}
.pl-cell {{
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  align-content: flex-start;
  min-height: 36px;
  min-width: 150px;
}}
.pl-empty {{
  color: #cbd5e1;
  font-size: 12px;
}}

/* ── Product badges ──────────────────────────────────── */
.pl-badge {{
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 500;
  line-height: 1;
  white-space: nowrap;
  cursor: default;
  transition: transform 0.1s, box-shadow 0.1s;
}}
.pl-badge:hover {{
  transform: translateY(-1px);
  box-shadow: 0 2px 6px rgba(0,0,0,0.08);
}}
.pl-dot {{
  width: 7px;
  height: 7px;
  border-radius: 50%;
  margin-right: 6px;
  flex-shrink: 0;
}}

/* ── Distribution section ────────────────────────────── */
.pl-dist {{
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 32px 28px;
  margin-top: 12px;
}}
.pl-dist-grid {{
  display: grid;
  grid-template-columns: 1fr;
  gap: 36px;
  margin-top: 20px;
}}
@media (min-width: 768px) {{
  .pl-dist-grid {{
    grid-template-columns: repeat(3, 1fr);
  }}
}}
.pl-dist-col h3 {{
  font-size: 14px;
  font-weight: 600;
  color: #334155;
  margin-bottom: 14px;
}}
.pl-dist-row {{
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 7px;
}}
.pl-dist-label {{
  font-size: 11px;
  color: #64748b;
  width: 120px;
  text-align: right;
  flex-shrink: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}}
.pl-dist-label-sm {{
  width: 90px;
}}
.pl-dist-track {{
  flex: 1;
  height: 14px;
  background: #f1f5f9;
  border-radius: 2px;
  overflow: hidden;
}}
.pl-dist-fill {{
  height: 100%;
  border-radius: 2px;
  transition: width 0.3s ease;
}}
.pl-dist-count {{
  font-size: 11px;
  font-weight: 500;
  color: #475569;
  width: 22px;
  text-align: right;
  flex-shrink: 0;
}}

/* ── Footer ──────────────────────────────────────────── */
.pl-footer {{
  padding: 20px 0;
  border-top: 1px solid #e2e8f0;
  margin-top: 16px;
}}
.pl-footer p {{
  font-size: 12px;
  color: #94a3b8;
}}

/* ── Function group badge colors ─────────────────────── */
{chr(10).join(fg_rules)}
"""


# ─────────────────────────────────────────────────────────────
# HTML body generation (for the Bob Swift HTML macro)
# ─────────────────────────────────────────────────────────────

def generate_html_body(products: list[dict]) -> str:
    """Generate the HTML body for the Bob Swift HTML macro.

    This uses CSS class names that match the stylesheet from generate_css().
    Paste this into the Bob Swift HTML macro body.
    """
    total = len(products)
    family_lines_in_data = list(OrderedDict.fromkeys(
        fl for fl in FAMILY_LINES if any(p["family_line"] == fl for p in products)
    ))
    function_groups_in_data = list(OrderedDict.fromkeys(
        fg for fg in FUNCTION_GROUPS if any(p["function_group"] == fg for p in products)
    ))

    fg_counts = Counter(p["function_group"] for p in products)
    type_counts = Counter(p["product_type"] for p in products)
    fl_counts = Counter(p["family_line"] for p in products)

    n_families = len(family_lines_in_data)
    n_types = len(set(p["product_type"] for p in products))
    n_groups = len(function_groups_in_data)

    def esc(s):
        return html.escape(s)

    def badge(product):
        cls = slug(product["function_group"])
        return (
            f'<span class="pl-badge fg-{cls}" title="{esc(product["name"])}'
            f'&#10;{esc(product["function_group"])} &middot; {esc(product["product_type"])}'
            f'&#10;{esc(product["family_line"])}">'
            f'<span class="pl-dot"></span>'
            f'{esc(product["name"])}'
            f'</span>'
        )

    def dist_bar(label, count, max_count, color, small_label=False):
        pct = (count / max_count * 100) if max_count > 0 else 0
        label_cls = "pl-dist-label pl-dist-label-sm" if small_label else "pl-dist-label"
        return (
            f'<div class="pl-dist-row">'
            f'<span class="{label_cls}">{esc(label)}</span>'
            f'<div class="pl-dist-track">'
            f'<div class="pl-dist-fill" style="width:{pct:.1f}%;background:{color}"></div>'
            f'</div>'
            f'<span class="pl-dist-count">{count}</span>'
            f'</div>'
        )

    parts = []

    # ── Wrapper ────────────────────────────────────────────
    parts.append('<div class="pl">')

    # ── Accent bar ─────────────────────────────────────────
    parts.append('<div class="pl-accent"></div>')

    # ── Header ─────────────────────────────────────────────
    parts.append('<div class="pl-header">')
    parts.append('  <p class="pl-eyebrow">Organization Overview</p>')
    parts.append('  <h1>Product Landscape</h1>')
    parts.append(
        f'  <p class="pl-subtitle">How our {total} products align across function groups, '
        f'product types, and family lines &mdash; a single view of the full portfolio.</p>'
    )
    parts.append('  <div class="pl-stats">')
    for val, label in [(total, "Products"), (n_families, "Family Lines"),
                       (n_types, "Product Types"), (n_groups, "Function Groups")]:
        parts.append(
            f'    <div class="pl-stat">'
            f'<span class="pl-stat-val">{val}</span>'
            f'<span class="pl-stat-lbl">{label}</span></div>'
        )
    parts.append('  </div>')
    parts.append('</div>')

    # ── Function Group Legend ──────────────────────────────
    parts.append('<div class="pl-legend">')
    parts.append('  <p class="pl-eyebrow">Function Groups</p>')
    parts.append('  <div class="pl-legend-items">')
    for fg in function_groups_in_data:
        cls = slug(fg)
        parts.append(
            f'    <span class="pl-legend-chip">'
            f'<span class="pl-legend-dot fg-{cls}"></span>'
            f'{esc(fg)}</span>'
        )
    parts.append('  </div>')
    parts.append('</div>')

    # ── Shape Key ─────────────────────────────────────────
    parts.append('<div class="pl-shapes">')
    parts.append('  <span class="pl-eyebrow">Product Types</span>')
    for pt in PRODUCT_TYPES:
        icon_entity = TYPE_SHAPES[pt][0]
        parts.append(
            f'  <span class="pl-shape-item">'
            f'<span class="pl-shape-icon">{icon_entity}</span> {esc(pt)}</span>'
        )
    parts.append('</div>')

    # ── Matrix Table ──────────────────────────────────────
    parts.append('<div class="pl-matrix-wrap">')
    parts.append('<table class="pl-matrix">')

    # Header
    parts.append('<thead><tr>')
    parts.append('  <th>Family Line</th>')
    for pt in PRODUCT_TYPES:
        icon_entity = TYPE_SHAPES[pt][0]
        pt_count = type_counts.get(pt, 0)
        parts.append(
            f'  <th>'
            f'<span class="pl-col-icon">{icon_entity}</span>'
            f'<span class="pl-col-title">{esc(pt)}</span><br/>'
            f'<span class="pl-col-count">{pt_count} products</span></th>'
        )
    parts.append('</tr></thead>')

    # Body rows
    parts.append('<tbody>')
    for fl in family_lines_in_data:
        fl_total = fl_counts.get(fl, 0)
        parts.append('<tr>')
        parts.append(
            f'  <td><span class="pl-row-title">{esc(fl)}</span>'
            f'<span class="pl-row-count">{fl_total} products</span></td>'
        )
        for pt in PRODUCT_TYPES:
            cell_products = get_products(products, fl, pt)
            if cell_products:
                inner = "".join(badge(p) for p in cell_products)
            else:
                inner = '<span class="pl-empty">&mdash;</span>'
            parts.append(f'  <td><div class="pl-cell">{inner}</div></td>')
        parts.append('</tr>')
    parts.append('</tbody>')
    parts.append('</table>')
    parts.append('</div>')

    # ── Distribution Summary ──────────────────────────────
    max_fg = max(fg_counts.values()) if fg_counts else 1
    max_type = max(type_counts.values()) if type_counts else 1
    max_fl = max(fl_counts.values()) if fl_counts else 1

    parts.append('<div class="pl-dist">')
    parts.append('  <p class="pl-eyebrow">Distribution Summary</p>')
    parts.append('  <div class="pl-dist-grid">')

    # By Function Group
    parts.append('    <div class="pl-dist-col">')
    parts.append('      <h3>By Function Group</h3>')
    for fg in sorted(function_groups_in_data, key=lambda x: -fg_counts.get(x, 0)):
        parts.append(f'      {dist_bar(fg, fg_counts[fg], max_fg, FUNCTION_COLORS[fg]["dot"])}')
    parts.append('    </div>')

    # By Product Type
    parts.append('    <div class="pl-dist-col">')
    parts.append('      <h3>By Product Type</h3>')
    for pt in sorted(PRODUCT_TYPES, key=lambda x: -type_counts.get(x, 0)):
        parts.append(f'      {dist_bar(pt, type_counts[pt], max_type, "#475569", small_label=True)}')
    parts.append('    </div>')

    # By Family Line
    parts.append('    <div class="pl-dist-col">')
    parts.append('      <h3>By Family Line</h3>')
    for fl in sorted(family_lines_in_data, key=lambda x: -fl_counts.get(x, 0)):
        parts.append(f'      {dist_bar(fl, fl_counts[fl], max_fl, "#818CF8")}')
    parts.append('    </div>')

    parts.append('  </div>')
    parts.append('</div>')

    # ── Footer ────────────────────────────────────────────
    parts.append('<div class="pl-footer">')
    parts.append(
        f'  <p>Product Landscape &middot; {total} Products &middot; '
        f'3 Classification Dimensions</p>'
    )
    parts.append('</div>')

    parts.append('</div>')  # close .pl wrapper

    return "\n".join(parts)


# ─────────────────────────────────────────────────────────────
# Standalone HTML (browser preview)
# ─────────────────────────────────────────────────────────────

def generate_standalone_html(products: list[dict]) -> str:
    """Full HTML document combining CSS + body for local preview."""
    css = generate_css()
    body = generate_html_body(products)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Product Landscape</title>
<style>
body {{ margin: 0; padding: 24px; background: #fff; }}
{css}
</style>
</head>
<body>
{body}
</body>
</html>"""


# ─────────────────────────────────────────────────────────────
# Confluence storage format (wraps in Bob Swift HTML + CSS macros)
# ─────────────────────────────────────────────────────────────

def generate_confluence_storage(products: list[dict]) -> str:
    """Generate Confluence storage format using Bob Swift HTML macro + CSS macro.

    This produces a page body with two Confluence macros:
      1. A CSS macro containing the stylesheet
      2. A Bob Swift HTML macro containing the HTML body
    """
    css = generate_css()
    body = generate_html_body(products)

    # CSS macro (bob swift)
    css_macro = (
        '<ac:structured-macro ac:name="css">\n'
        '<ac:plain-text-body><![CDATA[\n'
        f'{css}\n'
        ']]></ac:plain-text-body>\n'
        '</ac:structured-macro>'
    )

    # HTML macro (bob swift)
    html_macro = (
        '<ac:structured-macro ac:name="html-bobswift">\n'
        '<ac:plain-text-body><![CDATA[\n'
        f'{body}\n'
        ']]></ac:plain-text-body>\n'
        '</ac:structured-macro>'
    )

    return f"{css_macro}\n\n{html_macro}"


# ─────────────────────────────────────────────────────────────
# Confluence REST API integration
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


def update_page(page_id: str, title: str, storage_body: str, current_version: int) -> dict:
    """Update a Confluence page with storage format content."""
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


def publish_to_confluence(products: list[dict]):
    """Publish the generated visualization to a Confluence page."""
    page_id = os.environ["CONFLUENCE_PAGE_ID"]

    print(f"Fetching current page {page_id}...")
    page = get_page(page_id)
    title = page["title"]
    current_version = page["version"]["number"]

    storage_content = generate_confluence_storage(products)

    print(f"Updating '{title}' (v{current_version} → v{current_version + 1})...")
    result = update_page(page_id, title, storage_content, current_version)
    new_version = result["version"]["number"]

    base_url = os.environ["CONFLUENCE_URL"].rstrip("/")
    page_url = f"{base_url}/pages/viewpage.action?pageId={page_id}"
    print(f"Done! Page updated to v{new_version}")
    print(f"View: {page_url}")


# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate Product Landscape for Confluence (Bob Swift HTML + CSS macros)")
    parser.add_argument("--csv", required=True, help="Path to products CSV file")
    parser.add_argument("--output", help="Write standalone HTML for browser preview")
    parser.add_argument("--confluence-html", metavar="FILE",
                        help="Write HTML body (paste into Bob Swift HTML macro)")
    parser.add_argument("--confluence-css", metavar="FILE",
                        help="Write CSS stylesheet (paste into CSS macro)")
    parser.add_argument("--publish", action="store_true",
                        help="Publish to Confluence via REST API (requires env vars)")
    args = parser.parse_args()

    # Load data
    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"Error: CSV file not found: {csv_path}", file=sys.stderr)
        sys.exit(1)

    products = load_products(str(csv_path))
    print(f"Loaded {len(products)} products from {csv_path}")

    # Standalone HTML preview
    if args.output:
        standalone = generate_standalone_html(products)
        Path(args.output).write_text(standalone, encoding="utf-8")
        print(f"Standalone HTML → {args.output} ({len(standalone):,} bytes)")

    # Confluence HTML body (for Bob Swift HTML macro)
    if args.confluence_html:
        body = generate_html_body(products)
        Path(args.confluence_html).write_text(body, encoding="utf-8")
        print(f"HTML body → {args.confluence_html} ({len(body):,} bytes)")

    # Confluence CSS (for CSS macro)
    if args.confluence_css:
        css = generate_css()
        Path(args.confluence_css).write_text(css, encoding="utf-8")
        print(f"CSS stylesheet → {args.confluence_css} ({len(css):,} bytes)")

    # Publish to Confluence
    if args.publish:
        required_vars = ["CONFLUENCE_URL", "CONFLUENCE_PAGE_ID", "CONFLUENCE_USER", "CONFLUENCE_TOKEN"]
        missing = [v for v in required_vars if not os.environ.get(v)]
        if missing:
            print(f"Error: Missing environment variables: {', '.join(missing)}", file=sys.stderr)
            for v in required_vars:
                print(f"  export {v}=...", file=sys.stderr)
            sys.exit(1)
        publish_to_confluence(products)

    if not any([args.output, args.confluence_html, args.confluence_css, args.publish]):
        print("\nUsage options:")
        print("  --output preview.html              Browser preview")
        print("  --confluence-html body.html         HTML for Bob Swift HTML macro")
        print("  --confluence-css styles.css         CSS for CSS macro")
        print("  --publish                           Push to Confluence via API")


if __name__ == "__main__":
    main()
