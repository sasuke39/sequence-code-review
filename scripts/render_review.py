#!/usr/bin/env python3
"""Render a fixed offline sequence review page from structured JSON (stdlib only)."""
import argparse
import html
import json
import re
from pathlib import Path
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[1]
KINDS = {'original': '原有', 'added': '新增', 'updated': '更新', 'deleted': '删除'}
def esc(value):
    return html.escape(str(value), quote=True)
def need(condition, message):
    if not condition:
        raise ValueError(message)
def link(file, line=None):
    return 'idea://open?' + urlencode({'file': file['path'], 'line': line or file['line']})
def validate(data):
    files = data['files']
    ids = [f['id'] for f in files]
    need(len(ids) == len(set(ids)), 'duplicate file id')
    for f in files:
        need(Path(f['path']).is_absolute(), 'file path must be absolute: ' + f['id'])
        need(isinstance(f['line'], int) and f['line'] > 0, 'invalid file line')
        need(f['kind'] in KINDS, 'invalid file kind')
    need(len({c['id'] for c in data['chains']}) == len(data['chains']), 'duplicate chain id')
    covered = set()
    for c in data['chains']:
        need(isinstance(c.get('description'), str) and c['description'].strip(), 'chain needs business description')
        actors = c['participants']
        need(len(actors) >= 2 and len(set(actors)) == len(actors), 'need distinct participants')
        for step in c['steps']:
            need(step['from'] in actors and step['to'] in actors, 'unknown participant')
            need(step['kind'] in KINDS and step['description'].strip(), 'step needs kind and business description')
            need(step['file'] in ids, 'step needs valid file')
            need(isinstance(step.get('line', 1), int) and step.get('line', 1) > 0, 'invalid step line')
            covered.add(step['file'])
        for fid in c.get('files', []):
            need(fid in ids, 'unknown supporting file: ' + fid)
            covered.add(fid)
    expected = {f['id'] for f in files if f.get('changed', True)}
    missing = sorted(expected - covered)
    need(not missing, 'unmapped changed files: ' + ', '.join(missing))
    return {'changedFiles': len(expected), 'mappedFiles': len(expected & covered), 'missing': missing,
            'basis': 'Input inventory only; independent Git snapshot verification is required.'}
def tw(text, cjk=14.5, ascii_=7.6):
    return sum(cjk if ord(ch) > 0x2e80 else ascii_ for ch in text)
def chunks(text, max_width):
    # 英文/数字/符号连续片段整体换行，中文逐字；行首不放标点
    tokens = re.findall(r"[A-Za-z0-9_.#()/=<>\-]+|.", text)
    lines, cur, w = [], '', 0
    for t in tokens:
        tkw = tw(t)
        if w + tkw > max_width and cur and t not in '，。；：、！？）】》,.;:)':
            lines.append(cur.rstrip()); cur, w = '', 0
            if t == ' ':
                continue
        cur += t; w += tkw
    return lines + [cur] if cur else ['']
def diagram(chain, files):
    actors = chain['participants']
    cid = esc(chain['id'])
    aw = {a: max(150, tw(a, 15, 8.5) + 40) for a in actors}
    margin_l = max(120, aw[actors[0]] / 2 + 24)
    margin_r = max(120, aw[actors[-1]] / 2 + 24)
    width = max(980, len(actors) * 280, margin_l + margin_r + 260 * (len(actors) - 1))
    gap = (width - margin_l - margin_r) / (len(actors) - 1)
    xs = {a: margin_l + i * gap for i, a in enumerate(actors)}
    y = 120
    bodies = []
    for n, s in enumerate(chain['steps'], 1):
        x1, x2 = xs[s['from']], xs[s['to']]
        selfcall = x1 == x2
        method, tag = s['method'], KINDS[s['kind']]
        badge_w = tw(tag, 12, 7) + 16
        total = badge_w + 8 + tw(method, 14, 8.2)
        if selfcall:
            room_r, room_l = width - x1 - 70, x1 - 70
            side = 'r' if room_r >= min(room_l, 260) else 'l'
            avail = min(380, room_r if side == 'r' else room_l)
            lines = chunks(s['description'], max(150, avail))
            block = max([total] + [tw(l) for l in lines])
            left = x1 + 48 if side == 'r' else x1 - 48 - block
        else:
            span = abs(x2 - x1)
            lines = chunks(s['description'], max(150, span - 40))
            left = (x1 + x2) / 2 - total / 2
            block = max([total] + [tw(l) for l in lines])
        cond = s.get('condition')
        top = y - 28
        if cond:
            y += 30
        # 步骤框：条件分支用虚线框住该步骤，标签贴在框上沿
        ay = y + 38 + len(lines) * 21
        bottom = ay + 22
        if cond:
            lo = min(x1, x2) - 56
            hi = max(x1, x2) + 56
            if selfcall:
                lo, hi = min(lo, left - 16), max(hi, left + block + 16)
            lo, hi = max(40, lo), min(width - 16, hi)
            label = '条件  ' + cond
            lw = min(hi - lo - 20, tw(label, 13.5, 8.2) + 26)
            bodies.append(f'<g class="cond"><rect class="cond-box" x="{lo}" y="{top+10}" width="{hi-lo}" height="{bottom-top-10}" rx="10"/><rect class="cond-tab" x="{lo+12}" y="{top}" width="{lw}" height="22" rx="6"/><text x="{lo+23}" y="{top+15}">{esc(label)}</text></g>')
        bodies.append(f'<g class="step"><circle class="num" cx="28" cy="{y-5}" r="11"/><text class="num-t" x="28" y="{y-1}" text-anchor="middle">{n}</text>')
        bodies.append(f'<rect class="badge {s["kind"]}" x="{left}" y="{y-19}" width="{badge_w}" height="24" rx="12"/><text class="badge-t {s["kind"]}" x="{left+badge_w/2}" y="{y-3}" text-anchor="middle">{tag}</text>')
        bodies.append(f'<a href="{esc(link(files[s["file"]], s.get("line")))}"><text class="code-link" x="{left+badge_w+8}" y="{y-2}">{esc(method)}</text></a>')
        for i, line in enumerate(lines):
            if selfcall:
                bodies.append(f'<text class="desc" x="{left}" y="{y+24+i*21}">{esc(line)}</text>')
            else:
                bodies.append(f'<text class="desc" x="{(x1+x2)/2}" y="{y+24+i*21}" text-anchor="middle">{esc(line)}</text>')
        cls = 'msg async' if s.get('async') else 'msg'
        if selfcall:
            path = f'M {x1} {y+8} h 34 v {len(lines)*21+22} h -34'
        else:
            path = f'M {x1} {ay} H {x2}'
        bodies.append(f'<path class="{cls}" d="{path}" marker-end="url(#arrow-{cid})"/></g>')
        y = bottom + 40
    height = y
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(chain["title"])}"><defs><marker id="arrow-{cid}" markerWidth="12" markerHeight="12" refX="10" refY="5" orient="auto"><path class="arrow-head" d="M1,1 L10,5 L1,9 z"/></marker></defs>']
    for a, x in xs.items():
        w = aw[a]
        svg.append(f'<line class="life" x1="{x}" y1="64" x2="{x}" y2="{height-16}"/><g class="actor"><rect x="{x-w/2}" y="20" width="{w}" height="44" rx="10"/><text x="{x}" y="47" text-anchor="middle">{esc(a)}</text></g>')
    return ''.join(svg + bodies + ['</svg>'])
def render(data):
    coverage = validate(data)
    files = {f['id']:f for f in data['files']}
    navigation, content = [], []
    for index, c in enumerate(data['chains'], 1):
        cid = 'chain-' + c['id']
        navigation.append(f'<li><a href="#{esc(cid)}"><span class="nav-number">{index:02d}</span><span class="nav-label">{esc(c["title"])}</span></a></li>')
        fileids = list(dict.fromkeys([s['file'] for s in c['steps']] + c.get('files', [])))
        rows = []
        for fid in fileids:
            f = files[fid]
            rows.append(f'<tr><td class="fid">{esc(fid)}</td><td><a href="{esc(link(f))}">{esc(Path(f["path"]).name)}:{f["line"]}</a><small>{esc(f["path"])}</small></td><td><span class="tag {f["kind"]}">{KINDS[f["kind"]]}</span>{esc(f["description"])}</td></tr>')
        content.append(f'<details class="chain" id="{esc(cid)}" open><summary><span class="idx">{index:02d}</span>{esc(c["title"])}</summary><p class="chain-description">{esc(c["description"])}</p><div class="toolbar"><button onclick="fit(this)">适应宽度</button><button onclick="zoom(this,.15)" aria-label="放大">＋</button><button onclick="zoom(this,-.15)" aria-label="缩小">－</button><span class="meta">{len(c["steps"])} 步 · {len(fileids)} 个文件</span></div><div class="canvas">{diagram(c,files)}</div><details class="diagram-files"><summary>本图全部文件（{len(fileids)}）</summary><table>{"".join(rows)}</table></details></details>')
    css = (ROOT/'assets/review.css').read_text()
    js = (ROOT/'assets/review-interactions.js').read_text()
    page = f'<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(data["title"])}</title><style>{css}</style><button class="sidebar-toggle" aria-expanded="true" aria-label="展开或收起目录">收起目录</button><aside><h2>{esc(data["title"])}</h2><ol class="nav-list">{"".join(navigation)}</ol></aside><main>{"".join(content)}</main><script>{js}</script></html>'
    return page, coverage
if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('data', type=Path)
    p.add_argument('--output', required=True, type=Path)
    args = p.parse_args()
    try:
        page, report = render(json.loads(args.data.read_text()))
    except (ValueError, KeyError, TypeError) as e:
        p.error(str(e))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(page)
    args.output.with_suffix('.coverage.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(args.output)
