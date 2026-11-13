"""Before/after check for clean-ups that must not change how anything looks.

Records, for every element on every screen (cover, share pop-up, each game in play, Rules, Settings, flipped modes, stress
states, Remi Medias and Landscape), its position, size and the styles that decide its look, at six screen sizes. Random
numbers are fixed so two runs show the same dice, puzzles and tiles; animations are off.

    python3 tests/style_snapshot.py save before            # snapshot of the build in the repo root -> tests/out/snap/before
    python3 tests/style_snapshot.py save before /tmp/old   # snapshot of another folder holding index.html
    python3 tests/style_snapshot.py save quick - iphone12,sideways   # only some sizes (- = the repo root)
    python3 tests/style_snapshot.py compare before after   # lists every difference; "0 differences" = identical

Two snapshots of the same build must compare equal (run that once to trust it).
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import start_server, launch, ROOT
from playwright.sync_api import sync_playwright

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'snap')
SIZES = {
    'iphone12': (390, 797, 1, (47, 34, 0, 0), 844),
    'small': (320, 568, 1, (0, 0, 0, 0), None),
    'sideways': (844, 390, 1, (0, 21, 47, 47), None),
    'ipad': (820, 1180, 1, (24, 20, 0, 0), None),
    'laptop': (1366, 657, 0, (0, 0, 0, 0), None),
    'short': (1280, 593, 0, (0, 0, 0, 0), None),
}
INIT = """(function(){var s=0x9e3779b9;Math.random=function(){s|=0;s=s+0x6D2B79F5|0;var t=Math.imul(s^s>>>15,1|s);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296};
try{window.Worker=undefined}catch(e){}
if(window===window.top){window.__SAFE={t:%d,b:%d,l:%d,r:%d};try{['kb','oth','ws','sdk','remi'].forEach(function(g){localStorage.setItem(g+'-rules-seen','1')})}catch(e){}}})()"""
SNAP = r"""(()=>{const P=['display','position','color','backgroundColor','backgroundImage','fontFamily','fontSize','fontWeight','lineHeight','letterSpacing','textTransform','textAlign','textShadow','boxShadow','opacity',
 'borderTopWidth','borderRightWidth','borderBottomWidth','borderLeftWidth','borderTopColor','borderTopStyle','borderTopLeftRadius','paddingTop','paddingRight','paddingBottom','paddingLeft',
 'marginTop','marginRight','marginBottom','marginLeft','rowGap','columnGap','cursor','overflowX','overflowY','whiteSpace','zIndex','transform','flexGrow','flexShrink','justifyContent','alignItems',
 'outlineStyle','visibility','touchAction','userSelect','filter','animationName'],Q=['content','display','position','backgroundColor','backgroundImage','width','height','boxShadow','opacity','transform','color'];
 const out={};const key=e=>{const p=[];while(e&&e!==document.documentElement){const sib=e.parentNode?[...e.parentNode.children].indexOf(e):0;p.unshift(e.tagName.toLowerCase()+(e.id?'#'+e.id:'')+(typeof e.className==='string'&&e.className.trim()?'.'+e.className.trim().split(/\s+/).sort().join('.'):'')+':'+sib);e=e.parentNode}return p.join(' > ')};
 const r1=v=>Math.round(v*2)/2;
 const all=[document.documentElement,...document.querySelectorAll('body, body *')].filter(e=>!/^(SCRIPT|STYLE|NOSCRIPT|TEMPLATE)$/.test(e.tagName)&&!e.closest('svg svg *'));
 all.forEach(e=>{if(e.closest('iframe'))return;const k=e===document.documentElement?'html':key(e);if(!e.getClientRects().length&&e!==document.documentElement){out[k]='(not shown)';return}
  const cs=getComputedStyle(e),r=e.getBoundingClientRect(),o={rect:[r1(r.left),r1(r.top),r1(r.width),r1(r.height)].join(',')};P.forEach(p=>o[p]=cs[p]);
  ['::before','::after'].forEach(ps=>{const c=getComputedStyle(e,ps);if(c.content&&c.content!=='none'&&c.content!=='normal')Q.forEach(p=>o[ps+' '+p]=c[p])});
  if(e.children.length===0&&e.textContent.trim())o.text=e.textContent.trim().slice(0,40);out[k]=o});return out})()"""
STRESS = {
    'kb': "S.w=999;S.l=999;S.best=216;NC=4;start();p=[[6,6,6],[5,5,5],[4,4,4],[6,6]];c=[[6,6,6],[5,5,5],[4,4,4],[3,3]];render('You destroyed 3 dice. Your turn: tap a column please.')",
    'oth': "S.w=999;S.l=999;S.t=99;render('You flipped 12 · CPU must pass · your move')",
    'sdk': "time=5025000;clockOn=false;best.easy=3723000;hintOn=true;render('Hint 12 · that one’s locked in')",
    'rem': """(()=>{const R=__remi,G=R.G;const melds=[];for(let c=0;c<4;c++){[[1,5],[6,9],[10,13]].forEach(([a,b],i)=>{const t=[];for(let n=a;n<=b;n++)t.push(c*13+n-1);melds.push({o:(c+i)%4,t})})}
  G.melds=melds;G.own=Array(106).fill(-1);melds.forEach(m=>m.t.forEach(id=>G.own[id]=m.o));const hand=[];for(let i=52;i<52+HN;i++)hand.push(i);G.pl[0].hand=hand;G.pl[0].opened=true;
  G.disc=[];for(let i=52+HN;i<100;i++)G.disc.push(i);G.pile=[100,101,102,103,104,105];[1,2,3].forEach(p=>{G.pl[p].hand=[];G.pl[p].opened=true});G.pl[0].score=-1250;G.pl[1].score=975;G.pl[2].score=1240;G.pl[3].score=-385;
  G.cur=0;G.phase='draw';G.tn=20;R.T.start=HN;G.atuBy=0;G.dbl=true})()""",
}


def save(name, root, only=None):
    port = start_server(8981, root)
    dest = os.path.join(OUT, name); os.makedirs(dest, exist_ok=True)
    pw = sync_playwright().start(); br = launch(pw)
    for size, (w, h, touch, safe, sh) in SIZES.items():
        if only and size not in only:
            continue
        kw = dict(viewport={'width': w, 'height': h}, has_touch=bool(touch), is_mobile=bool(touch), reduced_motion='reduce')
        if sh:
            kw['screen'] = {'width': w, 'height': sh}
        ctx = br.new_context(**kw); ctx.add_init_script(INIT % safe)
        page = ctx.new_page(); errs = []
        page.on('pageerror', lambda e: errs.append(str(e))); page.on('console', lambda m: m.type == 'error' and errs.append(m.text))
        page.goto(f'http://127.0.0.1:{port}/index.html'); page.wait_for_timeout(700)
        res = {}
        gf = lambda: [x for x in page.frames if x != page.main_frame and x.evaluate("!!document.querySelector('main')&&document.querySelector('main').getClientRects().length>0")][0]

        def snap(tag, f=None):
            page.wait_for_timeout(150); res[tag] = (f or page).evaluate(SNAP)

        snap('cover')
        page.click('#logoT'); snap('cover share'); page.click('#shClose')
        for g in ['kb', 'oth', 'ws', 'sdk', 'rem']:
            page.click(f'.card[data-g="{g}"]'); page.wait_for_timeout(1300)
            f = gf()
            f.evaluate("(()=>{const p=document.getElementById('panel');if(p&&!p.hidden){const b=document.querySelector('#bar button[aria-expanded=true]');b&&b.click()}})()")
            click = lambda sel: f.evaluate("(s)=>{const e=document.querySelector(s);e&&e.click()}", sel)
            byText = lambda t: f.evaluate("(t)=>{const e=[...document.querySelectorAll('main button')].find(b=>b.textContent.trim()===t&&!b.disabled);e&&e.click()}", t)
            if g == 'rem':
                for _ in range(40):
                    ph = f.evaluate("__remi.G.phase")
                    if ph == 'dbl':
                        byText('Play')
                    elif ph in ('draw', 'play'):
                        break
                    page.wait_for_timeout(300)
            snap(g, f)
            if g == 'kb':
                click('.side.you .col.can'); page.wait_for_timeout(2800)
            elif g == 'oth':
                click('#board .sq.can'); page.wait_for_timeout(2800)
            elif g == 'ws':
                click('.tube'); snap(g + ' picked', f); f.evaluate("document.querySelectorAll('.tube')[8].click()"); page.wait_for_timeout(700)
            elif g == 'sdk':
                f.evaluate("(()=>{const i=val.findIndex(v=>!v);cells[i].click();keys[sol[i]].click();const j=val.findIndex(v=>!v);cells[j].click()})()")
                click('#aNotes'); f.evaluate("keys[3].click();keys[7].click()")
            elif g == 'rem':
                if f.evaluate("__remi.G.phase") == 'draw':
                    byText('Draw')
                page.wait_for_timeout(300); click('#rack .tl')
            snap(g + ' played', f)
            click('#bRules'); snap(g + ' rules', f)
            click('#bSet'); snap(g + ' settings', f)
            click('#bSet')
            if g in STRESS:
                for hn in ([15, 26] if g == 'rem' else [0]):
                    f.evaluate(STRESS[g].replace('HN', str(hn)))
                    if g == 'rem':
                        byText('Sort')
                    snap(f'{g} stress{hn or ""}', f)
            if g in ('kb', 'oth'):
                f.evaluate("mode='2p';document.body.classList.add('flip');start()"); snap(g + ' flip', f)
                click('.col.can, .sq.can'); page.wait_for_timeout(900); snap(g + ' flip played', f)
                click('#bSet'); snap(g + ' flip settings', f); click('#bSet')
                f.evaluate("mode='cpu';document.body.classList.remove('flip');start()")
            if g == 'rem':
                click('#bSet'); f.evaluate("document.querySelectorAll('#sSkin button')[1].click()"); snap('rem medias settings', f)
                click('#bSet'); snap('rem medias', f)
                click('#bRules'); snap('rem medias rules', f); click('#bRules')
                click('#bSet'); f.evaluate("document.querySelectorAll('#sLay button')[1].click()"); page.wait_for_timeout(400); snap('rem land', f)
                click('#bSet'); snap('rem land settings', f)
                click('#bRules'); snap('rem land rules', f); click('#bRules')
                f.evaluate(STRESS['rem'].replace('HN', '26')); byText('Sort'); snap('rem land stress26', f)
            page.evaluate("kbShowCover()"); page.wait_for_timeout(400)
        res['errors'] = errs
        json.dump(res, open(os.path.join(dest, size + '.json'), 'w'))
        print(name, size, 'screens', len(res) - 1, 'elements', sum(len(v) for k, v in res.items() if k != 'errors'), 'errors', errs[:2], flush=True)
        ctx.close()
    br.close(); pw.stop()


def tidy(scr):
    """A pseudo-element that isn't drawn is the same as none."""
    out = {}
    for k, v in scr.items():
        if isinstance(v, dict):
            v = dict(v)
            for ps in ('::before', '::after'):
                if v.get(ps + ' display') == 'none':
                    for p in [p for p in v if p.startswith(ps + ' ')]:
                        del v[p]
        out[k] = v
    return out


def compare(a, b, limit=60):
    total = 0; groups = {}
    for size in SIZES:
        if not (os.path.exists(os.path.join(OUT, a, size + '.json')) and os.path.exists(os.path.join(OUT, b, size + '.json'))):
            continue
        A = json.load(open(os.path.join(OUT, a, size + '.json'))); B = json.load(open(os.path.join(OUT, b, size + '.json')))
        for scr in sorted(set(A) | set(B)):
            if scr == 'errors':
                if A[scr] != B[scr]:
                    print('console errors differ', size, A[scr][:2], B[scr][:2]); total += 1
                continue
            x, y = A.get(scr), B.get(scr)
            if x is None or y is None:
                print('screen only in one snapshot:', size, scr); total += 1; continue
            x, y = tidy(x), tidy(y)
            for k in sorted(set(x) | set(y)):
                u, v = x.get(k), y.get(k)
                if u == v:
                    continue
                if not isinstance(u, dict) or not isinstance(v, dict):
                    d = [('shown', str(u)[:20] if not isinstance(u, dict) else 'shown', str(v)[:20] if not isinstance(v, dict) else 'shown')]
                else:
                    d = [(p, u.get(p), v.get(p)) for p in sorted(set(u) | set(v)) if u.get(p) != v.get(p)]
                for p, m, n in d:
                    total += 1
                    el = k.split(' > ')[-1].rsplit(':', 1)[0]
                    groups.setdefault((scr.split(' ')[0], el, p), []).append((size + ':' + scr, str(m)[:60], str(n)[:60]))
    for (g, el, p), where in sorted(groups.items(), key=lambda t: -len(t[1]))[:limit]:
        print(f'{len(where):4d}x {g} | {el} | {p}: {where[0][1]}  ->  {where[0][2]}   e.g. {where[0][0]}')
    if len(groups) > limit:
        print('... and', len(groups) - limit, 'more kinds')
    print(total, 'differences')
    return total


if __name__ == '__main__':
    if sys.argv[1] == 'save':
        save(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] != '-' else ROOT, sys.argv[4].split(',') if len(sys.argv) > 4 else None)
    else:
        sys.exit(1 if compare(sys.argv[2], sys.argv[3]) else 0)
