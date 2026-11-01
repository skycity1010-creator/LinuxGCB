#!/usr/bin/env python3
"""由原始 Excel/Word 基準檔產生條目清單 HTML：置頂搜尋框（輸入條目 ID 自動跳轉）。
內容為基準原文（項次、TWGCB-ID、類別、名稱、說明、設定方法、GCB 設定值），不含實機檢核結果。"""
import html, pathlib, re, sys, zipfile
from collections import Counter
from xml.etree import ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
      'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
XLSX = next(p for p in ROOT.glob('*.xlsx') if not p.name.startswith('~$'))
DOCX = next(ROOT.glob('*.docx'))

def xlsx_rows():
    z = zipfile.ZipFile(XLSX)
    strings = []
    if 'xl/sharedStrings.xml' in z.namelist():
        ss = ET.fromstring(z.read('xl/sharedStrings.xml'))
        strings = [''.join(t.text or '' for t in si.findall('.//m:t', NS))
                   for si in ss.findall('m:si', NS)]
    def val(c):
        v = c.find('m:v', NS)
        if v is None:
            return ''
        return strings[int(v.text)] if c.get('t') == 's' else (v.text or '')
    wb = ET.fromstring(z.read('xl/workbook.xml'))
    names = [s.get('name') for s in wb.findall('.//m:sheet', NS)]
    out = []
    for i, name in enumerate(names, 1):
        sh = ET.fromstring(z.read(f'xl/worksheets/sheet{i}.xml'))
        for r in sh.findall('.//m:row', NS):
            cells = {m.group(): val(c) for c in r.findall('m:c', NS)
                     if (m := re.match(r'[A-Z]+', c.get('r') or ''))}
            gid = cells.get('B', '')
            if re.fullmatch(r'TWGCB-\d{2}-\d{3}-\d{4}', gid):
                out.append(dict(sheet=name, ordinal=cells.get('A', ''), gcb_id=gid,
                                category=cells.get('C', ''), title=cells.get('D', ''),
                                description=cells.get('E', ''), method=cells.get('F', ''),
                                expected=cells.get('G', '').replace('\n', ' ')))
    return out

def docx_rows():
    """Word 說明文件表格列：回傳 {gcb_id: row}（同 ID 取首現列）。"""
    z = zipfile.ZipFile(DOCX)
    xml = ET.fromstring(z.read('word/document.xml'))
    out = {}
    for tr in xml.findall('.//w:tr', NS):
        cells = ['\n'.join(''.join(t.text or '' for t in p.findall('.//w:t', NS))
                           for p in cell.findall('.//w:p', NS)) for cell in tr.findall('w:tc', NS)]
        gid = next((c.strip() for c in cells if re.fullmatch(r'TWGCB-\d{2}-\d{3}-\d{4}', c.strip())), None)
        if gid and gid not in out and len(cells) >= 7:
            out[gid] = dict(sheet='（Word 說明文件）', ordinal=cells[0].strip(), gcb_id=gid,
                            category=cells[2].strip(), title=cells[3].strip(),
                            description=cells[4].strip(), method=cells[5].strip(),
                            expected=cells[6].strip().replace('\n', ' '))
    return out

rows = xlsx_rows()
word = docx_rows()
excel_ids = {r['gcb_id'] for r in rows}
missing_in_excel = sorted(set(word) - excel_ids)
missing_in_word = sorted(excel_ids - set(word))
for gid in missing_in_excel:
    w = dict(word[gid])
    w['flag'] = 'Excel 列表缺漏：僅見於 Word 說明文件'
    rows.append(w)
rows.sort(key=lambda r: r['gcb_id'])
for r in rows:
    r.setdefault('flag', '')
sheets = Counter(r['sheet'] for r in rows)
cats = Counter(r['category'] for r in rows)

def esc(s):
    return html.escape(str(s)).replace('\n', '<br>')

cards = []
for r in rows:
    n = r['gcb_id'].split('-')[-1]
    flag = f'<div class="flag">⚠ {esc(r["flag"])}</div>' if r['flag'] else ''
    cards.append(f'''<tr class="entry{' flagged' if r['flag'] else ''}" id="e{n}" data-id="{n} {r['gcb_id']}" data-cat="{esc(r['category'])}" data-sheet="{esc(r['sheet'])}">
<td><a class="anchor" href="#e{n}">{n}</a></td>
<td class="num">{esc(r['ordinal'])}</td>
<td>{esc(r['category'])}<span class="sheet">{esc(r['sheet'])}</span></td>
<td>{flag}{esc(r['title'])}<span class="sheet">{esc(r['gcb_id'])}</span></td>
<td class="expected"><b>{esc(r['expected'])}</b></td>
<td class="desc">{esc(r['description'])}</td>
<td class="method">{esc(r['method'])}</td>
</tr>''')

sheet_badges = ''.join(f'<span>{esc(k)} {v}</span>' for k, v in sheets.items())
cat_opts = ''.join(f'<option value="{esc(k)}">{esc(k)}（{v}）</option>' for k, v in cats.items())

page = f'''<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>RHEL9 政府組態基準 v1.2 條目清單（原始 Excel/Word）</title>
<style>
* {{ box-sizing: border-box; }}
body {{ font-family: "Noto Sans TC", system-ui, sans-serif; margin: 0; background: #f6f7f9; color: #111827; }}
header.top {{ position: sticky; top: 0; z-index: 10; background: #111827; color: #fff; padding: 10px 16px;
  display: flex; flex-wrap: wrap; gap: 10px; align-items: center; box-shadow: 0 2px 8px rgba(0,0,0,.25); }}
header.top h1 {{ font-size: 15px; margin: 0 12px 0 0; font-weight: 600; }}
#search {{ flex: 1 1 260px; max-width: 420px; padding: 8px 12px; border-radius: 8px; border: 0; font-size: 15px; }}
#cat {{ padding: 7px 10px; border-radius: 8px; border: 0; font-size: 13px; }}
#hint {{ font-size: 12px; color: #9ca3af; }}
.summary {{ font-size: 12px; display: flex; gap: 8px; flex-wrap: wrap; }}
.summary span {{ padding: 2px 8px; border-radius: 999px; background: #1f2937; }}
main {{ max-width: 1400px; margin: 0 auto; padding: 16px; }}
table {{ width: 100%; border-collapse: collapse; background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,.1); }}
th, td {{ border: 1px solid #e5e7eb; padding: 8px 10px; font-size: 13px; vertical-align: top; text-align: left; }}
thead th {{ position: sticky; top: 64px; z-index: 5; background: #1f2937; color: #fff; font-size: 13px; }}
tr.entry {{ scroll-margin-top: 100px; }}
tr.entry:nth-child(even) {{ background: #f9fafb; }}
tr.entry.flash {{ outline: 3px solid #2563eb; outline-offset: -3px; }}
tr.flagged {{ background: #fffbeb !important; }}
.flag {{ color: #b45309; font-weight: 600; font-size: 12px; margin-bottom: 3px; }}
a.anchor {{ color: #2563eb; text-decoration: none; font-weight: 600; }}
td.num {{ text-align: right; color: #6b7280; }}
td.expected {{ white-space: nowrap; }}
td.desc, td.method {{ white-space: pre-wrap; word-break: break-word; min-width: 260px; max-width: 420px; }}
.sheet {{ display: block; font-size: 11px; color: #9ca3af; font-weight: 400; }}
.hidden {{ display: none; }}
</style>
</head>
<body>
<header class="top">
<h1>RHEL9 政府組態基準 v1.2 條目清單（原始）</h1>
<input id="search" type="search" placeholder="輸入條目 ID（如 0187、TWGCB-01-012-0187）自動跳轉；輸入關鍵字過濾" autofocus>
<select id="cat"><option value="">全部類別（{len(cats)}）</option>{cat_opts}</select>
<span id="hint"></span>
<div class="summary">{sheet_badges}<span>共 {len(rows)} 條</span>{f'<span>⚠ Excel 缺漏 {len(missing_in_excel)} 條（已自 Word 補入）：{",".join(g.split("-")[-1] for g in missing_in_excel)}</span>' if missing_in_excel else '<span>Excel/Word 條目一致</span>'}</div>
</header>
<main>
<table>
<thead><tr><th>ID</th><th>項次</th><th>類別</th><th>原則設定名稱</th><th>GCB 設定值</th><th>說明</th><th>設定方法</th></tr></thead>
<tbody>
{''.join(cards)}
</tbody>
</table>
</main>
<script>
const entries = [...document.querySelectorAll('.entry')];
const search = document.getElementById('search');
const cat = document.getElementById('cat');
const hint = document.getElementById('hint');
function resolve(id) {{
  const q = id.trim().toLowerCase();
  if (!q) return null;
  const digits = q.replace(/[^0-9]/g, '');
  for (const e of entries) {{
    const ids = e.dataset.id.toLowerCase().split(/\\s+/);
    if (ids.some(v => v === q || v === digits)) return e;
  }}
  if (digits.length) {{
    const d4 = digits.length <= 4 ? digits.padStart(4, '0') : digits;
    return entries.find(e => e.dataset.id.toLowerCase().includes(d4)) || null;
  }}
  return null;
}}
let lastFlash = null;
function apply() {{
  const q = search.value.trim().toLowerCase();
  const c = cat.value;
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
    const hit = (!c || e.dataset.cat === c) && (!q || e.dataset.id.includes(q) || e.textContent.toLowerCase().includes(q));
    e.classList.toggle('hidden', !hit);
    if (hit) shown++;
  }}
  hint.textContent = (q || c) ? `符合 ${{shown}} 條` : '';
}}
search.addEventListener('input', apply);
cat.addEventListener('change', apply);
search.addEventListener('keydown', ev => {{ if (ev.key === 'Enter') ev.preventDefault(); }});
</script>
</body>
</html>'''

out = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT/'reports/entry_list_20261101.html'
out.write_text(page)
print('written', out, len(rows), 'entries |', dict(sheets),
      '| Excel 缺漏自 Word 補入:', missing_in_excel or '無',
      '| Word 缺漏:', missing_in_word or '無')
