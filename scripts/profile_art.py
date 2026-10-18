"""Build the profile's repository-owned SVGs from public GitHub contributions.

Daily use: python scripts/profile_art.py
Portrait: python scripts/profile_art.py --portrait (requires Pillow locally)
"""
import argparse
import datetime as dt
import html
import http.client
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
USER = 'TMBilalTM'
BG, PANEL, BORDER, TEXT, MUTED, BLUE = '#0d1117', '#111923', '#263646', '#e6edf3', '#8b9daf', '#83b6d4'


def svg(width, height, title, body):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{html.escape(title, quote=True)}">
<title>{html.escape(title)}</title><style>text{{font-family:ui-monospace,SFMono-Regular,Consolas,monospace}}.reveal{{animation:in .55s both}}@keyframes in{{from{{opacity:0;transform:translateY(5px)}}to{{opacity:1;transform:translateY(0)}}}}@media(prefers-reduced-motion:reduce){{.reveal{{animation:none}}}}</style>
<rect x="1" y="1" width="{width-2}" height="{height-2}" rx="16" fill="{BG}" stroke="{BORDER}"/>{body}</svg>'''


def text(x, y, value, color=TEXT, size=13, extra=''):
    return f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" {extra}>{html.escape(str(value))}</text>'


def write(name, content):
    (ROOT / name).write_text(content, encoding='utf-8')


def card():
    body = ''.join(f'<circle cx="{25+i*17}" cy="25" r="4" fill="{c}"/>' for i,c in enumerate(['#ff7b72','#e3b341','#7ee787']))
    body += text(90, 30, 'bilal@github: ~', MUTED, 12)
    body += f'<path d="M1 48H549" stroke="{BORDER}"/>'
    body += text(27, 87, '$ neofetch --about bilal', BLUE, 15)
    body += text(27, 125, 'BILAL AKSOY', TEXT, 28, 'font-weight="700"')
    body += text(27, 150, 'Developer from Cyprus', MUTED, 14)
    rows = [('Focus', 'Building / Automating / Learning'), ('Now', 'KKTCOF / DarkGiveaway'), ('Code', 'PHP / JS / SQL / Python'), ('Ops', 'Server Management'), ('Web', 'bilaltm.live'), ('Mail', 'bilpcukbilo@gmail.com')]
    for i,(key,val) in enumerate(rows):
        body += f'<g class="reveal" style="animation-delay:{.18+i*.13}s">' + text(27,199+i*30,key,BLUE,13) + text(107,199+i*30,val,TEXT,13) + '</g>'
    body += text(27, 399, 'Creating tools that help others', MUTED, 12)
    body += text(27, 419, 'learn and automate everyday tasks.', MUTED, 12)
    write('info-card.svg', svg(550,450,'Bilal Aksoy — developer, projects and contact',body))
    body = text(30,43,'~/TMBilalTM',BLUE,16) + text(30,85,'BUILD. AUTOMATE. KEEP LEARNING.',TEXT,28,'font-weight="700"')
    body += text(30,115,'A little curiosity. A lot of things to build.',MUTED,14)
    body += text(850,43,'01 / PROFILE',MUTED,11,'text-anchor="end"')
    write('terminal-header.svg',svg(900,145,'TMBilalTM — Build. Automate. Keep learning.',body))


def portrait():
    from PIL import Image
    im = Image.open(ROOT/'bilaltm_foto.gif').convert('RGB').resize((74,58))
    ramp = ' .:-=+*#%@'
    body = text(22,30,'$ cat portrait.ascii',BLUE,12)
    for y in range(58):
        line = ''
        for x in range(74):
            r,g,b = im.getpixel((x,y))
            # The supplied flat blue background is intentionally blank.
            background = b > r*1.12 and g > r*1.1
            light = (r*.299+g*.587+b*.114)/255
            line += ' ' if background else ramp[min(9,int((1-light)*9))]
        clip = f'row{y}'
        body += f'<clipPath id="{clip}"><rect x="18" y="{48+y*6.3}" width="314" height="8"><animate attributeName="width" from="0" to="314" dur=".25s" begin="{y*.025:.3f}s" fill="freeze"/></rect></clipPath>'
        body += f'<text xml:space="preserve" x="18" y="{55+y*6.3}" font-size="7" letter-spacing="0" fill="{TEXT}" clip-path="url(#{clip})">{html.escape(line)}</text>'
    body += text(22,430,'bilaltm_foto.gif → ASCII',MUTED,11)
    write('bilal-ascii.svg', svg(350,450,'ASCII portrait generated from Bilal’s supplied GIF',body))


class CalendarParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cells, self.tooltips, self.active = {}, {}, None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get('data-date') and 'data-level' in a:
            self.cells[a['data-date']] = {'date':a['data-date'],'level':int(a['data-level']),'id':a.get('id')}
        if tag == 'tool-tip':
            self.active = a.get('for')

    def handle_data(self, data):
        if self.active:
            self.tooltips[self.active] = self.tooltips.get(self.active,'') + data

    def handle_endtag(self, tag):
        if tag == 'tool-tip':
            self.active = None


def fetch():
    req = urllib.request.Request(f'https://github.com/users/{USER}/contributions',headers={'User-Agent':'TMBilalTM-profile-art','Accept':'text/html'})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req,timeout=45) as response:
                document = response.read().decode()
            break
        except (OSError, http.client.HTTPException):
            if attempt == 2:
                raise
            time.sleep(2)
    parser = CalendarParser()
    parser.feed(document)
    days = []
    for day in sorted(parser.cells.values(),key=lambda d:d['date']):
        tooltip = parser.tooltips.get(day.pop('id'),'').strip()
        match = re.search(r'([\d,]+) contributions?\b',tooltip)
        if match:
            day['count'] = int(match.group(1).replace(',',''))
        elif re.search(r'No contributions?\b',tooltip):
            day['count'] = 0
        else:
            raise ValueError(f'Cannot parse contribution count for {day["date"]}')
        days.append(day)
    if not 350 <= len(days) <= 371 or len({d['date'] for d in days}) != len(days):
        raise ValueError('Unexpected calendar; preserving previous output')
    today = dt.datetime.now(dt.timezone.utc).date().isoformat()
    days = [d for d in days if d['date'] <= today]
    data = {'username':USER,'through':days[-1]['date'],'days':days,'total':sum(d['count'] for d in days)}
    (ROOT/'data').mkdir(exist_ok=True)
    write('data/contributions.json',json.dumps(data,indent=2)+'\n')
    return data


def heatmap(data):
    days = data['days']
    start = dt.date.fromisoformat(days[0]['date'])
    start -= dt.timedelta(days=(start.weekday()+1)%7)
    palette = ['#17232e','#233f53','#365f7b','#588daf',BLUE]
    body = text(30,36,'$ git log --contributions',BLUE,14)
    body += text(870,36,'PUBLIC GITHUB ACTIVITY',MUTED,11,'text-anchor="end"')
    body += text(25,99,'M',MUTED,10)+text(25,127,'W',MUTED,10)+text(25,155,'F',MUTED,10)
    seen = set()
    for day in days:
        date = dt.date.fromisoformat(day['date'])
        offset = (date-start).days
        week, weekday = divmod(offset,7)
        x,y = 48+week*15,70+weekday*14
        if date.month not in seen:
            body += text(x,59,date.strftime('%b'),MUTED,10)
            seen.add(date.month)
        body += f'<rect class="reveal" style="animation-delay:{(week+weekday)*.014:.3f}s" x="{x}" y="{y}" width="11" height="10" rx="2" fill="{palette[min(4,day["level"])]}"><title>{day["date"]}: {day["count"]} contributions</title></rect>'
    total = data['total']
    active = sum(d['count'] > 0 for d in days)
    best = max(d['count'] for d in days)
    body += text(30,202,f'{total:,} contributions  /  {active} active days  /  {best} best day',TEXT,13)
    body += text(30,230,f'Calendar through {data["through"]} · refreshed daily via GitHub Actions',MUTED,11)
    body += text(741,230,'Less',MUTED,10)
    for i,c in enumerate(palette):
        body += f'<rect x="{772+i*14}" y="221" width="10" height="10" rx="2" fill="{c}"/>'
    body += text(846,230,'More',MUTED,10)
    write('contrib-heatmap.svg',svg(900,253,'Real GitHub contribution calendar for '+USER,body))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--portrait',action='store_true')
    p.add_argument('--cached',action='store_true')
    args = p.parse_args()
    if args.portrait:
        portrait()
        card()
    else:
        heatmap(json.loads((ROOT/'data/contributions.json').read_text()) if args.cached else fetch())
