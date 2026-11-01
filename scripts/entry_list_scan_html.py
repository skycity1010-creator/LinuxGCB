#!/usr/bin/env python3
"""（備用）由 R29 實機檢核結果產生條目清單 HTML：含 PASS/FAIL 徽章。主清單請用 entry_list_html.py（原始 Excel/Word 版）。"""
import json, html, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
controls = json.load(open(ROOT/'data/controls.json'))
registry = {r['gcb_id']: r for r in json.load(open(ROOT/'data/scope_registry.json'))}
scan = json.load(open(ROOT/'data/realhost_scan_20261101_r29.json'))
results = {c['id']: c['result'] for c in scan['checks']}
policies = {}
for p in (ROOT/'policies').glob('*.yml'):
    for c in json.loads(p.read_text())['checks']:
        policies[c['id']] = c
PARTIAL = {108, 141, 269, 270}
ACCEPTED = {187, 229}

rows = []
for c in controls:
    n = int(c['gcb_id'].split('-')[-1])
    reg = registry[c['gcb_id']]
    sca = reg['sca_id']
    if not reg['included']:
        state = 'EXCLUDED'
    elif n in PARTIAL:
        state = 'MANUAL_PENDING'
    else:
        state = 'PASS' if results.get(sca) == 'passed' else 'FAIL'
    pol = policies.get(sca, {})
    rows.append(dict(
        n=f'{n:04d}', gcb_id=c['gcb_id'], sca_id=sca, category=c['category'],
        title=c['title'], expected=c.get('expected', ''),
        state=state, profile=reg.get('profile', ''),
        description=pol.get('description', ''), rationale=pol.get('rationale', ''),
        method=c.get('configuration_method', ''),
        accepted=n in ACCEPTED, partial=n in PARTIAL,
    ))

counts = {}
for r in rows:
    counts[r['state']] = counts.get(r['state'], 0) + 1

def esc(s):
    return html.escape(str(s)).replace('\n', '<br>')

cards = []
for r in rows:
    badge = {'PASS': 'PASS', 'FAIL': 'FAIL', 'MANUAL_PENDING': '範圍保留', 'EXCLUDED': '不適用'}[r['state']]
    extra = ' accepted' if r['accepted'] else ''
    compliance = r['description'] or f"合規值: {r['expected']}"
    manual = r['rationale'] or f"人工檢核程序（來源）：{r['method'][:600]}"
    cards.append(f'''<section class="entry {r['state'].lower()}{extra}" id="e{r['n']}" data-id="{r['n']} {r['gcb_id']} {r['sca_id']}" data-cat="{esc(r['category'])}">
<h2><a class="anchor" href="#e{r['n']}">#{r['n']}</a> {esc(r['title'])}
<span class="badge {r['state'].lower()}">{badge}</span>{'<span class="badge accepted">Accepted finding</span>' if r['accepted'] else ''}
<span class="meta">{esc(r['category'])}｜{esc(r['gcb_id'])}｜SCA {r['sca_id']}｜{esc(r['profile'])}</span></h2>
<p class="compliance">{esc(compliance)}</p>
<details><summary>人工檢核</summary><pre>{esc(manual)}</pre></details>
</section>''')

page = f'''<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>RHEL9 GCB v1.2 條目清單（307 條 VERIFIED／R29 2026-11-01）</title>
<style>
:root {{ --pass:#1a7f37; --fail:#b91c1c; --pend:#a16207; --excl:#6b7280; }}
* {{ box-sizing: border-box; }}
body {{ font-family: "Noto Sans TC", system-ui, sans-serif; margin: 0; background: #f6f7f9; color: #111827; }}
header.top {{ position: sticky; top: 0; z-index: 10; background: #111827; color: #fff; padding: 10px 16px;
  display: flex; flex-wrap: wrap; gap: 10px; align-items: center; box-shadow: 0 2px 8px rgba(0,0,0,.25); }}
header.top h1 {{ font-size: 15px; margin: 0 12px 0 0; font-weight: 600; }}
#search {{ flex: 1 1 260px; max-width: 420px; padding: 8px 12px; border-radius: 8px; border: 0; font-size: 15px; }}
#hint {{ font-size: 12px; color: #9ca3af; }}
.summary {{ font-size: 12px; display: flex; gap: 8px; flex-wrap: wrap; }}
.summary span {{ padding: 2px 8px; border-radius: 999px; background: #1f2937; }}
main {{ max-width: 980px; margin: 0 auto; padding: 16px; }}
.entry {{ background: #fff; border-radius: 10px; padding: 14px 18px; margin: 12px 0; border-left: 6px solid var(--excl); scroll-margin-top: 130px; }}
.entry.pass {{ border-left-color: var(--pass); }} .entry.fail {{ border-left-color: var(--fail); }}
.entry.manual_pending {{ border-left-color: var(--pend); }}
.entry.flash {{ outline: 3px solid #2563eb; outline-offset: 2px; }}
h2 {{ font-size: 16px; margin: 0 0 6px; }}
a.anchor {{ color: #2563eb; text-decoration: none; }}
.badge {{ font-size: 11px; padding: 2px 8px; border-radius: 999px; color: #fff; vertical-align: middle; margin-left: 6px; }}
.badge.pass {{ background: var(--pass); }} .badge.fail {{ background: var(--fail); }}
.badge.manual_pending {{ background: var(--pend); }} .badge.excluded {{ background: var(--excl); }}
.badge.accepted {{ background: #7c3aed; }}
.meta {{ display: block; font-size: 11px; color: #6b7280; font-weight: 400; margin-top: 2px; }}
.compliance {{ font-size: 14px; margin: 4px 0; }}
details {{ font-size: 13px; }} pre {{ white-space: pre-wrap; background: #f3f4f6; padding: 8px; border-radius: 6px; }}
.hidden {{ display: none; }}
</style>
</head>
<body>
<header class="top">
<h1>RHEL9 GCB v1.2 條目清單</h1>
<input id="search" type="search" placeholder="輸入條目 ID（如 0187、900187、TWGCB-01-012-0187）自動跳轉；輸入關鍵字過濾" autofocus>
<span id="hint"></span>
<div class="summary">
<span>PASS {counts.get('PASS',0)}</span><span>FAIL {counts.get('FAIL',0)}</span>
<span>範圍保留 {counts.get('MANUAL_PENDING',0)}</span><span>不適用 {counts.get('EXCLUDED',0)}</span>
<span>共 {len(rows)} 條｜VERIFIED 2026-11-01｜R29</span>
</div>
</header>
<main>
{''.join(cards)}
</main>
<script>
const entries = [...document.querySelectorAll('.entry')];
const search = document.getElementById('search');
const hint = document.getElementById('hint');
function resolve(id) {{
  const q = id.trim().toLowerCase();
  if (!q) return null;
  const digits = q.replace(/[^0-9]/g, '');
  let target = null;
  for (const e of entries) {{
    const ids = e.dataset.id.toLowerCase().split(/\\s+/);
    if (ids.some(v => v === q || v === digits)) {{ target = e; break; }}
  }}
  if (!target && digits.length) {{
    const d4 = digits.length <= 4 ? digits.padStart(4, '0') : digits;
    target = entries.find(e => e.dataset.id.toLowerCase().includes(d4)) || null;
  }}
  return target;
}}
let lastFlash = null;
search.addEventListener('input', () => {{
  const q = search.value.trim().toLowerCase();
  const t = resolve(search.value);
  const exactId = t && (t.dataset.id.toLowerCase().split(/\\s+/).some(v => v === q || v === q.replace(/[^0-9]/g, '')));
  if (exactId) {{
    for (const e of entries) e.classList.remove('hidden');
    hint.textContent = `跳轉至 ${{t.id.slice(1)}}`;
    t.scrollIntoView({{behavior: 'smooth', block: 'start'}});
    if (lastFlash) lastFlash.classList.remove('flash');
    t.classList.add('flash'); lastFlash = t;
    history.replaceState(null, '', '#' + t.id);
    return;
  }}
  let shown = 0;
  for (const e of entries) {{
    const hit = !q || e.dataset.id.includes(q) || e.textContent.toLowerCase().includes(q);
    e.classList.toggle('hidden', !hit);
    if (hit) shown++;
  }}
  hint.textContent = q ? `符合 ${{shown}} 條` : '';
}});
search.addEventListener('keydown', ev => {{ if (ev.key === 'Enter') ev.preventDefault(); }});
</script>
</body>
</html>'''

out = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT/'reports/entry_list_scan_20261101.html'
out.write_text(page)
print('written', out, len(rows), 'entries', counts)
