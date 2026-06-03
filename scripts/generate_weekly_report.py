#!/usr/bin/env python3
"""
generate_weekly_report.py — Weekly intelligence report.

Generates an HTML report with:
  - Sector overview (obs count, engagement %)
  - Top performing patterns this period
  - Winning formulas (content_type + pattern + occasion)
  - Visual DNA insights
  - Content gaps and recommendations
  - Account leaderboard

Usage:
  python3 scripts/generate_weekly_report.py                    # generate report
  python3 scripts/generate_weekly_report.py --output report.html  # custom output
"""
import json, os, sys, argparse
from datetime import datetime
from pathlib import Path

import psycopg2
import psycopg2.extras

DB_URL = os.environ.get("DATABASE_URL", "postgresql://ogz:ogz_local_dev@localhost:5432/ogz_knowledge")
REPO = Path(__file__).parent.parent


def generate():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    now = datetime.now().strftime("%Y-%m-%d")

    # 1. Overall stats
    cur.execute("SELECT count(*) as total, count(*) FILTER (WHERE engagement_potential = 'high') as high FROM observations")
    overall = cur.fetchone()

    # 2. By sector
    cur.execute("""
        SELECT sector, count(*) as total,
            count(*) FILTER (WHERE engagement_potential = 'high') as high,
            round(100.0 * count(*) FILTER (WHERE engagement_potential = 'high') / count(*)) as high_pct
        FROM observations GROUP BY sector ORDER BY high_pct DESC
    """)
    sectors = cur.fetchall()

    # 3. Top patterns (all sectors)
    cur.execute("""
        SELECT pm->>'pattern_slug' as pattern, count(*) as total,
            round(100.0 * count(*) FILTER (WHERE engagement_potential = 'high') / count(*)) as high_pct
        FROM observations, jsonb_array_elements(pattern_matches) as pm
        GROUP BY pm->>'pattern_slug' HAVING count(*) >= 5
        ORDER BY high_pct DESC LIMIT 15
    """)
    top_patterns = cur.fetchall()

    # 4. Winning formulas
    cur.execute("""
        SELECT content_type, pm->>'pattern_slug' as pattern, occasion,
            count(*) as total,
            round(100.0 * count(*) FILTER (WHERE engagement_potential = 'high') / count(*)) as high_pct
        FROM observations, jsonb_array_elements(pattern_matches) as pm
        GROUP BY content_type, pm->>'pattern_slug', occasion
        HAVING count(*) >= 5 AND round(100.0 * count(*) FILTER (WHERE engagement_potential = 'high') / count(*)) >= 75
        ORDER BY total DESC LIMIT 10
    """)
    formulas = cur.fetchall()

    # 5. Visual DNA
    cur.execute("""
        SELECT visual_observations->>'lighting' as lighting,
               visual_observations->>'setting' as setting,
               count(*) as total,
               round(100.0 * count(*) FILTER (WHERE engagement_potential = 'high') / count(*)) as high_pct
        FROM observations
        GROUP BY 1, 2 HAVING count(*) >= 10
        ORDER BY high_pct DESC LIMIT 8
    """)
    visuals = cur.fetchall()

    # 6. Content gaps
    cur.execute("""
        SELECT sector, content_type, count(*) as total
        FROM observations GROUP BY sector, content_type
        ORDER BY total ASC LIMIT 8
    """)
    gaps = cur.fetchall()

    # 7. Account leaderboard
    cur.execute("""
        SELECT account_handle_normalized as account, sector, count(*) as total,
            round(100.0 * count(*) FILTER (WHERE engagement_potential = 'high') / count(*)) as high_pct
        FROM observations GROUP BY 1, 2 HAVING count(*) >= 10
        ORDER BY high_pct DESC LIMIT 10
    """)
    accounts = cur.fetchall()

    cur.close()
    conn.close()

    # Build HTML
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>OGZ Intelligence Report — {now}</title>
<style>
body {{ font-family: -apple-system, sans-serif; background: #0a0a0a; color: #e0e0e0; padding: 32px; max-width: 900px; margin: 0 auto; }}
h1 {{ color: #F0BE5E; font-size: 24px; border-bottom: 1px solid #252525; padding-bottom: 12px; }}
h2 {{ color: #F0BE5E; font-size: 18px; margin-top: 32px; }}
table {{ width: 100%; border-collapse: collapse; margin: 12px 0; }}
th {{ text-align: left; padding: 8px; border-bottom: 2px solid #F0BE5E; font-size: 12px; color: #999; }}
td {{ padding: 8px; border-bottom: 1px solid #252525; font-size: 14px; }}
.gold {{ color: #F0BE5E; font-weight: 600; }}
.stat {{ display: inline-block; text-align: center; padding: 16px 24px; background: #151515; border-radius: 8px; margin: 4px; }}
.stat .n {{ font-size: 32px; font-weight: 700; color: #F0BE5E; }}
.stat .l {{ font-size: 11px; color: #777; }}
.badge {{ display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 11px; }}
.high {{ background: #0a2e0a; color: #4ade80; }}
.low {{ background: #2e0a0a; color: #f87171; }}
.footer {{ margin-top: 40px; padding-top: 16px; border-top: 1px solid #252525; font-size: 12px; color: #555; }}
</style></head><body>
<h1>OGZ Content Intelligence Report</h1>
<p style="color:#777">Generated {now} · {overall['total']} observations · {len(sectors)} sectors</p>

<div style="margin: 20px 0">
  <div class="stat"><div class="n">{overall['total']}</div><div class="l">Total Observations</div></div>
  <div class="stat"><div class="n">{overall['high']}</div><div class="l">High Engagement</div></div>
  <div class="stat"><div class="n">{round(100 * overall['high'] / overall['total'])}%</div><div class="l">Overall Rate</div></div>
  <div class="stat"><div class="n">{len(top_patterns)}</div><div class="l">Active Patterns</div></div>
</div>

<h2>Sector Performance</h2>
<table><tr><th>Sector</th><th>Obs</th><th>High</th><th>Rate</th></tr>
{''.join(f"<tr><td>{s['sector']}</td><td>{s['total']}</td><td>{s['high']}</td><td class='gold'>{s['high_pct']}%</td></tr>" for s in sectors)}
</table>

<h2>Top 15 Patterns</h2>
<table><tr><th>Pattern</th><th>Obs</th><th>High %</th></tr>
{''.join(f"<tr><td>{p['pattern']}</td><td>{p['total']}</td><td class='gold'>{p['high_pct']}%</td></tr>" for p in top_patterns)}
</table>

<h2>Winning Formulas (75%+ high engagement)</h2>
<table><tr><th>Content Type</th><th>Pattern</th><th>Occasion</th><th>Obs</th><th>High %</th></tr>
{''.join(f"<tr><td>{f['content_type']}</td><td>{f['pattern']}</td><td>{f['occasion']}</td><td>{f['total']}</td><td class='gold'>{f['high_pct']}%</td></tr>" for f in formulas)}
</table>

<h2>Visual DNA (best lighting + setting combos)</h2>
<table><tr><th>Lighting</th><th>Setting</th><th>Obs</th><th>High %</th></tr>
{''.join(f"<tr><td>{v['lighting']}</td><td>{v['setting']}</td><td>{v['total']}</td><td class='gold'>{v['high_pct']}%</td></tr>" for v in visuals)}
</table>

<h2>Content Gaps (underserved)</h2>
<table><tr><th>Sector</th><th>Content Type</th><th>Obs</th><th>Opportunity</th></tr>
{''.join(f"<tr><td>{g['sector']}</td><td>{g['content_type']}</td><td>{g['total']}</td><td><span class='badge low'>underserved</span></td></tr>" for g in gaps)}
</table>

<h2>Account Leaderboard</h2>
<table><tr><th>Account</th><th>Sector</th><th>Obs</th><th>High %</th></tr>
{''.join(f"<tr><td>@{a['account']}</td><td>{a['sector']}</td><td>{a['total']}</td><td class='gold'>{a['high_pct']}%</td></tr>" for a in accounts)}
</table>

<div class="footer">
  OGZ Content Intelligence · Auto-generated from {overall['total']} benchmark observations<br>
  Data source: ogz-knowledge (rabie011/ogz-knowledge) · API: port 4100
</div>
</body></html>"""

    return html


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    html = generate()

    out_path = args.output or str(REPO / "logs" / "reports" / f"intelligence_report_{datetime.now().strftime('%Y%m%d')}.html")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    with open(out_path, "w") as f:
        f.write(html)

    print(f"✅ Report generated: {out_path}")
    print(f"   Open in browser: file://{os.path.abspath(out_path)}")


if __name__ == "__main__":
    main()
