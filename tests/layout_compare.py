"""Compare the template layout of the working index.html with a committed one (default: HEAD).

    python3 tests/layout_compare.py            # working index.html vs HEAD
    python3 tests/layout_compare.py main~1     # vs another commit

For every game (and Knucklebones/Othello flipped 2-player) at iphone12, small, big, sideways and desk it measures,
in stage units (offsetTop chains inside #app, so scaling and rotation don't matter): the title, the second
flipped title and the bar, plus any element outside the 390-wide stage. Prints only differences, elements
outside the stage and console errors. Expected template: title 0-64, bar 731-767, flipped second title 667-731.
"""
import json, os, subprocess, sys, tempfile
from harness import ROOT, GAMES, start_server, open_page, open_game, to_cover

MEAS = """(()=>{const app=document.getElementById('app');
 const off=e=>{let x=0,y=0,n=e;while(n&&n!==app){x+=n.offsetLeft;y+=n.offsetTop;n=n.offsetParent}return n===app?[x,y,x+e.offsetWidth,y+e.offsetHeight]:null};
 const pick={title:document.querySelector('main>h1:not(#t2)')||document.querySelector('.ttl1'),t2:document.querySelector('#t2,.ttl2'),bar:document.getElementById('bar')};
 const o={};for(const k in pick){const e=pick[k];if(e&&e.offsetParent)o[k]=off(e)}
 const W=app.offsetWidth,H=app.offsetHeight,out=[];
 document.querySelectorAll('main *').forEach(e=>{if(!e.offsetParent||e.closest('#panel'))return;const r=off(e);if(!r)return;
  if(r[0]<-1||r[1]<-1||r[2]>W+1||r[3]>H+1)out.push((e.id||e.className||e.tagName)+':'+r.join(','))});
 o.size=[W,H];o.outside=out.slice(0,5);return o})()"""


def measure(root, port):
    start_server(port, root)
    res = {}
    for size in ['iphone12', 'small', 'big', 'sideways', 'desk']:
        pw, b, page = open_page(port, size)
        for g in GAMES:
            f = open_game(page, g)
            res[f'{size} {g}'] = f.evaluate(MEAS)
            if g in ('kb', 'oth'):
                f.evaluate("mode='2p';document.body.classList.add('flip');start()")
                page.wait_for_timeout(300)
                res[f'{size} {g} flip'] = f.evaluate(MEAS)
                f.evaluate("mode='cpu';document.body.classList.remove('flip');start()")
            to_cover(page)
        res[f'{size} errors'] = page.errors
        b.close(); pw.stop()
    return res


if __name__ == '__main__':
    ref = sys.argv[1] if len(sys.argv) > 1 else 'HEAD'
    old_dir = tempfile.mkdtemp()
    with open(os.path.join(old_dir, 'index.html'), 'wb') as fh:
        fh.write(subprocess.check_output(['git', '-C', ROOT, 'show', f'{ref}:index.html']))
    old, new = measure(old_dir, 8831), measure(ROOT, 8832)
    diffs = [k for k in new if old.get(k) != new[k]]
    for k in diffs:
        print('DIFF', k, '\n  old', old.get(k), '\n  new', new[k])
    for k, v in new.items():
        if isinstance(v, dict) and v.get('outside'):
            print('OUTSIDE', k, v['outside'])
    print(f'{len(new)} screens checked against {ref}: {len(diffs)} differences')
    print('iPhone 12 Knucklebones:', new['iphone12 kb'], '\nflipped:', new['iphone12 kb flip'])
