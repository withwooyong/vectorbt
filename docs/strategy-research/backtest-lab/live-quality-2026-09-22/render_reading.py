"""Render the three bounded reading documents to local, dependency-free HTML."""
import base64
import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCES = {
    ROOT / 'README.md': 'report.html',
    ROOT.parent / 'results-extension-2026-09-21/interpretation.md': 'results.html',
    ROOT.parent / 'results-extension-2026-09-21/strategy-annual-totals.md': 'counts.html',
}
NAV = '<nav><a href="report.html">현재 데이터 품질·매수 조건</a> · <a href="results.html">실험 결과 해석</a> · <a href="counts.html">전략별 매수·매도 횟수</a></nav>'
STYLE = 'body{max-width:1100px;margin:32px auto;padding:0 22px;font:16px/1.8 system-ui,sans-serif;color:#202630}h1{font-size:28px}h2{margin-top:38px}table{border-collapse:collapse;width:100%;font-size:14px;margin:18px 0}td,th{border:1px solid #ccd3dc;padding:9px;text-align:left}th{background:#eef3fa}a{color:#145bc1}nav{background:#eef3fa;padding:14px}img{max-width:100%;height:auto}code{overflow-wrap:anywhere}section{overflow-x:auto}'


def inline(text, source):
    text = html.escape(text)
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)

    def link(match):
        label, target = match.groups()
        path = (source.parent / html.unescape(target)).resolve()
        href = SOURCES.get(path)
        if href is None:
            import os
            href = os.path.relpath(path, ROOT).replace('\\', '/')
        return f'<a href="{html.escape(href, quote=True)}">{label}</a>'

    return re.sub(r'\[([^\]]+)\]\(([^)]+)\)', link, text)


def render(source):
    out, table, listing = [], False, False
    for line in source.read_text(encoding='utf-8').splitlines():
        if not line.startswith('|') and table:
            out.append('</tbody></table></section>')
            table = False
        item = re.match(r'^(?:- |\d+\. )(.*)', line)
        if not item and listing:
            out.append('</ul>')
            listing = False
        if not line.strip():
            continue
        if line.startswith('|'):
            cells = [x.strip() for x in line.strip('|').split('|')]
            if all(re.fullmatch(r':?-+:?', x) for x in cells):
                continue
            tag = 'td' if table else 'th'
            if not table:
                out.append('<section><table><tbody>')
                table = True
            out.append('<tr>' + ''.join(f'<{tag}>{inline(x, source)}</{tag}>' for x in cells) + '</tr>')
        elif line.startswith('#'):
            level = len(line) - len(line.lstrip('#'))
            out.append(f'<h{level}>{inline(line[level:].strip(), source)}</h{level}>')
        elif line.startswith('!['):
            match = re.fullmatch(r'!\[([^\]]*)\]\(([^)]+)\)', line)
            alt, file = match.groups()
            data = base64.b64encode((source.parent / file).read_bytes()).decode()
            out.append(f'<img alt="{html.escape(alt)}" src="data:image/png;base64,{data}">')
        elif item:
            if not listing:
                out.append('<ul>')
                listing = True
            out.append('<li>' + inline(item[1], source) + '</li>')
        else:
            out.append('<p>' + inline(line, source) + '</p>')
    if table:
        out.append('</tbody></table></section>')
    if listing:
        out.append('</ul>')
    return '<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>' + html.escape(source.read_text(encoding='utf-8').splitlines()[0].lstrip('# ')) + '</title><style>' + STYLE + '</style><body>' + NAV + '\n'.join(out) + '</body></html>'


if __name__ == '__main__':
    for source, name in SOURCES.items():
        (ROOT / name).write_text(render(source), encoding='utf-8')
        print(name)
