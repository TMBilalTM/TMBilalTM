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
    rows = [('Focus', 'Building / Automating / Learning'), ('Now', 'KKTCOF / DarkGiveaway'), ('Code', 'PHP / JS / SQL / Python'), ('Ops', 'Server Management'), ('Web', 'bilaltm.tech'), ('Mail', 'bilpcukbilo@gmail.com')]
    for i,(key,val) in enumerate(rows):
        body += f'<g class="reveal" style="animation-delay:{.18+i*.13}s">' + text(27,199+i*30,key,BLUE,13) + text(107,199+i*30,val,TEXT,13) + '</g>'
    write('profile-card.svg', svg(550,450,'Bilal Aksoy — developer, projects and contact',body))
    body = text(30,43,'~/TMBilalTM',BLUE,16) + text(30,85,'BUILD. AUTOMATE. KEEP LEARNING.',TEXT,28,'font-weight="700"')
    body += text(30,115,'A little curiosity. A lot of things to build.',MUTED,14)
    body += text(850,43,'01 / PROFILE',MUTED,11,'text-anchor="end"')
    write('terminal-header.svg',svg(900,145,'TMBilalTM — Build. Automate. Keep learning.',body))


def portrait():
    from PIL import Image
    # Enlarge the subject and keep the light shirt readable on a dark canvas.
    im = Image.open(ROOT/'bilaltm_foto.gif').convert('RGB').crop((65,130,535,600)).resize((74,55))
    ramp = ' .:coO0#%@'
    body = text(22,30,'$ whoami',BLUE,12)
    for y in range(55):
        line = ''
        for x in range(74):
            r,g,b = im.getpixel((x,y))
            background = abs(r-131)+abs(g-178)+abs(b-206) < 48
            light = (r*.299+g*.587+b*.114)/255
            line += ' ' if background else ramp[max(4,min(9,int((1-light)*9)))]
        clip = f'row{y}'
        start, end = .02+y*.003, .04+y*.003
        body += f'<clipPath id="{clip}"><rect x="19" y="{56+y*6.5}" width="312" height="10"><animate attributeName="width" values="0;0;312;312;0" keyTimes="0;{start:.3f};{end:.3f};0.94;1" dur="12s" repeatCount="indefinite"/></rect></clipPath>'
        body += f'<text xml:space="preserve" x="19" y="{64+y*6.5}" font-size="7.4" textLength="310" lengthAdjust="spacingAndGlyphs" fill="{TEXT}" clip-path="url(#{clip})">{html.escape(line)}</text>'
    write('portrait-loop.svg', svg(350,450,'Bilal Aksoy',body))


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


def snake_game(foods, valid):
    """Simulate a snake that navigates to food using shortest legal paths."""
    from collections import deque
    snake = [(x,3) for x in range(5,-1,-1)]
    remaining = set(foods)
    states, eaten = [list(snake)], {}
    direction = (1,0)
    for tick in range(3000):
        if not remaining:
            break
        # Prefer a turn on equal-distance routes so clusters feel responsive.
        dx,dy = direction
        directions = [(-dy,dx),(dy,-dx),(dx,dy),(-dx,-dy)]
        blocked = set(snake[:-1]) | ({snake[-1]} if snake[-1] in remaining else set())
        queue = deque([snake[0]])
        parents = {snake[0]:None}
        target = None
        while queue:
            point = queue.popleft()
            if point in remaining and point != snake[0]:
                target = point
                break
            for ux,uy in directions:
                nxt = (point[0]+ux,point[1]+uy)
                if nxt in valid and nxt not in blocked and nxt not in parents:
                    parents[nxt] = point
                    queue.append(nxt)
        if target is not None:
            step = target
            while parents[step] != snake[0]:
                step = parents[step]
        else:
            options = [(snake[0][0]+ux,snake[0][1]+uy) for ux,uy in directions]
            step = next((p for p in options if p in valid and p not in blocked),None)
            if step is None:
                raise ValueError('Snake has no legal move')
        grows = step in remaining and len(snake) < 10
        assert step not in (snake if grows else snake[:-1]), 'Self collision'
        direction = (step[0]-snake[0][0],step[1]-snake[0][1])
        snake = [step]+(snake if grows else snake[:-1])
        if step in remaining:
            remaining.remove(step)
            eaten[step] = len(states)
        states.append(list(snake))
    if remaining:
        raise ValueError('Snake could not reach all contribution cells')
    return states,eaten


def heatmap(data):
    days = data['days']
    start = dt.date.fromisoformat(days[0]['date'])
    start -= dt.timedelta(days=(start.weekday()+1)%7)
    palette = ['#17232e','#233f53','#365f7b','#588daf',BLUE]
    body = text(30,36,'$ snake --contributions',BLUE,14)
    cells = {}
    for day in days:
        date = dt.date.fromisoformat(day['date'])
        week, weekday = divmod((date-start).days,7)
        if date.day == 1:
            body += text(48+week*15,63,date.strftime('%b'),MUTED,10)
        cells[(week,weekday)] = day
    foods = {p for p,d in cells.items() if d['count'] > 0}
    states,eaten = snake_game(foods,set(cells))
    step_seconds = .145
    travel = (len(states)-1)*step_seconds
    duration = travel+2
    fade_out, reset = (travel+.7)/duration, (travel+1.2)/duration
    for (col,row),day in cells.items():
        x,y = 48+col*15,76+row*16
        base = palette[min(4,day['level'])]
        anim = ''
        if (col,row) in eaten:
            t = eaten[(col,row)]*step_seconds/duration
            anim = f'<animate attributeName="fill" values="{base};{base};{palette[0]};{palette[0]};{base};{base}" keyTimes="0;{max(.00001,t-.0001):.7f};{t:.7f};{reset:.7f};{reset+.001:.7f};1" dur="{duration:.3f}s" repeatCount="indefinite"/>'
        body += f'<rect x="{x}" y="{y}" width="11" height="11" rx="2" fill="{base}"><title>{day["date"]}: {day["count"]} contributions</title>{anim}</rect>'
    times = [i*step_seconds/duration for i in range(len(states))]+[1]
    timing = ';'.join(f'{t:.7f}' for t in times)
    fade = f'<animate attributeName="opacity" values="1;1;0;0;1" keyTimes="0;{fade_out:.7f};{reset:.7f};0.999;1" dur="{duration:.3f}s" repeatCount="indefinite"/>'
    body += '<g>'+fade
    for i in range(9,-1,-1):
        pts = [state[min(i,len(state)-1)] for state in states]
        pts.append(pts[-1])
        positions = ';'.join(f'{53.5+c*15} {81.5+r*16}' for c,r in pts)
        c,r = pts[0]
        shape = f'<rect x="-5" y="-5" width="10" height="10" rx="3" fill="{BLUE}" opacity="{1-i*.05:.2f}"/>'
        if i == 0:
            shape = f'<path d="M-8 0 C-8-6 -5-9 0-9 C6-9 9-5 9 0 C9 6 5 9 0 9 C-6 9-8 6-8 0Z" fill="#ffc787" stroke="{BG}" stroke-width="1.4"/><ellipse cx="-2.8" cy="-1" rx=".7" ry="1.25" fill="#080808"/><ellipse cx="3" cy="-1" rx=".7" ry="1.25" fill="#080808"/>'
        visibility = ';'.join('1' if len(state)>i else '0' for state in states)
        visibility += ';'+visibility.split(';')[-1]
        body += f'<g transform="translate({53.5+c*15} {81.5+r*16})">{shape}<animateTransform attributeName="transform" type="translate" values="{positions}" keyTimes="{timing}" calcMode="linear" dur="{duration:.3f}s" repeatCount="indefinite"/><animate attributeName="opacity" values="{visibility}" keyTimes="{timing}" calcMode="discrete" dur="{duration:.3f}s" repeatCount="indefinite"/></g>'
    body += '</g>'+text(30,237,f'{data["total"]:,} public contributions',TEXT,12)
    write('avatar-snake.svg',svg(900,263,'Contribution snake with Bilal’s character head',body))


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
