"""The one page: HTML, FAIL and UNSURE rows first. UNSURE counts as FAIL in the totals; no rows is not a pass."""
import html
import json


def render(rows):
    bad = [r for r in rows if r["verdict"] != "PASS"]
    good = [r for r in rows if r["verdict"] == "PASS"]
    head = f"FAIL: {len(bad)} PASS: {len(good)}" if rows else "FAIL: no rows, nothing was judged PASS: 0"
    body = "".join(
        f"<tr><td>{html.escape(r['verdict'])}</td><td>{html.escape(str(r['req']))}</td><td>{html.escape(r['check'])}</td>"
        f"<td>{html.escape(r['kind'])}</td><td>{r['tick']}</td><td><code>{html.escape(json.dumps(r['numbers'], sort_keys=True))}</code></td></tr>\n"
        for r in bad + good)
    return f"<!doctype html><html><body><h1>{head}</h1><table>\n{body}</table></body></html>\n"
