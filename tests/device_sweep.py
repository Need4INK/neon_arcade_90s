"""Device sweep: the cover, the share pop-up, every game, Rules, Settings, both flipped modes, Remi Medias and Landscape,
plus stress states (big scores, long messages, 4x3 Knucklebones, Remi hands of 15/26/38 tiles) at 36 screen sizes:
phones upright and sideways, tablets, laptop and desktop windows. Checks that nothing is cut off by the screen, leaves the
stage or overlaps, that no label is clipped, that panels fit, and that there are no console errors.

    python3 tests/device_sweep.py                      # all 36 sizes, about 25 min
    python3 tests/device_sweep.py se1_320x568 laptop_1366x657

Prints one line per size and the problems found; screenshots and the raw numbers go to tests/out/sweep/.
Expected to scroll (not problems): Remi's and Sudoku's Rules.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import start_server, launch, close_panel, game_frame
from playwright.sync_api import sync_playwright

SHOTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'sweep')
os.makedirs(SHOTS, exist_ok=True)
# name: (w, h, touch, safe(t,b,l,r), screen_h or None)
DEV = {
 # phones, portrait
 'fold_cover_280x653': (280, 653, 1, (0, 0, 0, 0), None),
 'se1_320x568': (320, 568, 1, (0, 0, 0, 0), None),
 'zfold_344x882': (344, 882, 1, (0, 0, 0, 0), None),
 'android_360x640': (360, 640, 1, (0, 0, 0, 0), None),
 'android_chrome_360x668': (360, 668, 1, (0, 0, 0, 0), None),
 'se3_safari_375x548': (375, 548, 1, (0, 0, 0, 0), None),
 'se3_app_375x647': (375, 647, 1, (20, 0, 0, 0), 667),
 'mini_app_375x762': (375, 762, 1, (50, 34, 0, 0), 812),
 'ip12_safari_390x664': (390, 664, 1, (0, 0, 0, 0), None),
 'ip12_app_390x797': (390, 797, 1, (47, 34, 0, 0), 844),
 'ip15_app_393x793': (393, 793, 1, (59, 34, 0, 0), 852),
 'pixel_chrome_412x785': (412, 785, 1, (0, 0, 0, 0), None),
 'pixel_app_412x867': (412, 867, 1, (0, 0, 0, 0), None),
 'promax_app_430x873': (430, 873, 1, (59, 34, 0, 0), 932),
 # phones, sideways
 'se1_land_568x320': (568, 320, 1, (0, 0, 0, 0), None),
 'se3_land_667x375': (667, 375, 1, (0, 0, 0, 0), None),
 'ip12_land_844x390': (844, 390, 1, (0, 21, 47, 47), None),
 'pixel_land_915x412': (915, 412, 1, (0, 0, 0, 0), None),
 # tablets
 'fold_open_673x841': (673, 841, 1, (0, 0, 0, 0), None),
 'ipadmini_744x1133': (744, 1133, 1, (24, 20, 0, 0), None),
 'ipad_810x1080': (810, 1080, 1, (24, 20, 0, 0), None),
 'ipadair_820x1180': (820, 1180, 1, (24, 20, 0, 0), None),
 'ipadpro_1024x1366': (1024, 1366, 1, (24, 20, 0, 0), None),
 'ipadmini_land_1133x744': (1133, 744, 1, (24, 20, 0, 0), None),
 'ipadair_land_1180x820': (1180, 820, 1, (24, 20, 0, 0), None),
 'ipadpro_land_1366x1024': (1366, 1024, 1, (24, 20, 0, 0), None),
 'ipad_split_590x820': (590, 820, 1, (24, 20, 0, 0), None),
 'ipad_slideover_320x780': (320, 780, 1, (24, 20, 0, 0), None),
 'tablet_land_short_960x540': (960, 540, 1, (0, 0, 0, 0), None),
 # laptops / desktop windows (mouse)
 'laptop_1280x593': (1280, 593, 0, (0, 0, 0, 0), None),
 'laptop_1366x657': (1366, 657, 0, (0, 0, 0, 0), None),
 'laptop_1440x789': (1440, 789, 0, (0, 0, 0, 0), None),
 'desk_1920x945': (1920, 945, 0, (0, 0, 0, 0), None),
 'desk_2560x1297': (2560, 1297, 0, (0, 0, 0, 0), None),
 'window_600x400': (600, 400, 0, (0, 0, 0, 0), None),
 'window_1000x300': (1000, 300, 0, (0, 0, 0, 0), None),
}

MEAS = r"""(()=>{const app=document.getElementById('app')||document.getElementById('cstage');const vw=innerWidth,vh=innerHeight;
 const ar=app.getBoundingClientRect(),k=Math.sqrt(ar.width*ar.height/(app.offsetWidth*app.offsetHeight));
 const name=e=>(e.id?'#'+e.id:'')+(e.className&&typeof e.className==='string'?'.'+e.className.trim().split(/\s+/).join('.'):'')||e.tagName;
 const vis=e=>{if(!e.getClientRects().length)return false;const s=getComputedStyle(e);return s.visibility!=='hidden'&&+s.opacity>0};
 const o={k:+k.toFixed(3),stage:[ar.left,ar.top,ar.right,ar.bottom].map(Math.round),vp:[vw,vh],offscreen:[],outstage:[],clip:[],overlap:[],minTap:[999,''],minFont:[999,'']};
 const all=[...document.querySelectorAll('main *, #cstage *')].filter(e=>vis(e)&&!e.closest('svg'));
 all.forEach(e=>{const r=e.getBoundingClientRect();if(r.width<1||r.height<1)return;
  if(e.closest('#sir')||e.closest('#table'))return; // scrolling areas
  if(r.left<-1||r.top<-1||r.right>vw+1||r.bottom>vh+1){if(o.offscreen.length<4)o.offscreen.push(name(e)+':'+[r.left,r.top,r.right,r.bottom].map(Math.round))}
  else if(r.left<ar.left-1||r.top<ar.top-1||r.right>ar.right+1||r.bottom>ar.bottom+1){if(o.outstage.length<4)o.outstage.push(name(e)+':'+[r.left,r.top,r.right,r.bottom].map(Math.round))}
  const cs=getComputedStyle(e);
  const own=[...e.childNodes].some(n=>n.nodeType===3&&n.textContent.trim());
  if(own){const f=parseFloat(cs.fontSize)*k;if(f<o.minFont[0])o.minFont=[+f.toFixed(1),name(e)+' "'+e.textContent.trim().slice(0,18)+'"']}
  if((e.scrollWidth>e.clientWidth+1||e.scrollHeight>e.clientHeight+2)&&e.clientWidth>0&&cs.display!=='inline'&&!e.matches('#panel,.panel,#rack,#board,main,#game,#cstage')&&(own||e.tagName==='BUTTON')){if(o.clip.length<5)o.clip.push(name(e)+' "'+e.textContent.trim().slice(0,22)+'" '+e.scrollWidth+'>'+e.clientWidth+' / '+e.scrollHeight+'>'+e.clientHeight)}
 });
 const btns=all.filter(e=>(e.tagName==='BUTTON'||e.getAttribute('role')==='button')&&!e.disabled);
 btns.forEach(e=>{const r=e.getBoundingClientRect(),m=Math.min(r.width,r.height);if(m<o.minTap[0])o.minTap=[+m.toFixed(1),name(e)+' "'+e.textContent.trim().slice(0,12)+'"']});
 const bb=all.filter(e=>e.tagName==='BUTTON'&&!e.closest('#panel')&&!e.closest('#sir')&&!e.classList.contains('meld'));
 for(let i=0;i<bb.length;i++)for(let j=i+1;j<bb.length;j++){if(bb[i].contains(bb[j])||bb[j].contains(bb[i]))continue;const a=bb[i].getBoundingClientRect(),b=bb[j].getBoundingClientRect();
  const w=Math.min(a.right,b.right)-Math.max(a.left,b.left),h=Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top);if(w>2&&h>2&&o.overlap.length<3)o.overlap.push(name(bb[i])+' x '+name(bb[j])+' '+Math.round(w)+'x'+Math.round(h))}
 const p=document.getElementById('panel');
 if(p&&!p.hidden){const r=p.getBoundingClientRect();o.panel={rect:[r.left,r.top,r.right,r.bottom].map(Math.round),scrolls:p.scrollHeight>p.clientHeight+1,sh:p.scrollHeight,ch:p.clientHeight,
   off:r.left<-1||r.top<-1||r.right>vw+1||r.bottom>vh+1,rows:[...p.querySelectorAll('.row')].filter(vis).filter(x=>x.scrollWidth>x.clientWidth+1).map(x=>x.textContent.trim().slice(0,20))}}
 return o})()"""

STRESS = {
 'kb': "S.w=999;S.l=999;S.best=216;NC=4;start();p=[[6,6,6],[5,5,5],[4,4,4],[6,6]];c=[[6,6,6],[5,5,5],[4,4,4],[3,3]];render('You destroyed 3 dice. Your turn: tap a column please.')",
 'oth': "S.w=999;S.l=999;S.t=99;render('You flipped 12 · CPU must pass · your move')",
 'sdk': "time=5025000;clockOn=true;best.easy=3723000;hintOn=true;render('Hint 12 · that one’s locked in')",
 'rem': """(()=>{const R=__remi,G=R.G;const melds=[];for(let c=0;c<4;c++){[[1,5],[6,9],[10,13]].forEach(([a,b],i)=>{const t=[];for(let n=a;n<=b;n++)t.push(c*13+n-1);melds.push({o:(c+i)%4,t})})}
  G.melds=melds;G.own=Array(106).fill(-1);melds.forEach(m=>m.t.forEach(id=>G.own[id]=m.o));
  const hand=[];for(let i=52;i<52+HN;i++)hand.push(i);G.pl[0].hand=hand;G.pl[0].opened=true;
  G.disc=[];for(let i=52+HN;i<100;i++)G.disc.push(i);G.pile=[100,101,102,103,104,105];
  [1,2,3].forEach(p=>{G.pl[p].hand=[];G.pl[p].opened=true});G.pl[0].score=-1250;G.pl[1].score=975;G.pl[2].score=1240;G.pl[3].score=-385;
  G.cur=0;G.phase='draw';G.tn=20;R.T.start=HN;G.atuBy=0;G.dbl=true})()""",
}


def run(names):
    port = start_server(8871)
    total = 0
    pw = sync_playwright().start()
    br = launch(pw)
    for name in names:
        w, h, touch, safe, sh = DEV[name]
        kw = dict(viewport={'width': w, 'height': h}, has_touch=bool(touch), is_mobile=bool(touch), device_scale_factor=2 if w < 1200 else 1)
        if sh:
            kw['screen'] = {'width': w, 'height': sh}
        ctx = br.new_context(**kw)
        t, b, l, r = safe
        ctx.add_init_script("if(window===window.top){window.__SAFE={t:%d,b:%d,l:%d,r:%d};try{['kb','oth','ws','sdk','remi'].forEach(function(g){localStorage.setItem(g+'-rules-seen','1')})}catch(e){}}" % (t, b, l, r))
        page = ctx.new_page()
        errs = []
        page.on('pageerror', lambda e: errs.append(str(e)))
        page.on('console', lambda m: m.type == 'error' and errs.append(m.text))
        page.goto(f'http://127.0.0.1:{port}/index.html')
        page.wait_for_timeout(700)
        res = {}
        full = name.endswith('797') or '_app_' in name

        def shot(tag):
            page.screenshot(path=f'{SHOTS}/{name}__{tag}.png', full_page=full)

        res['cover'] = page.evaluate(MEAS)
        res['cover']['full'] = page.evaluate("document.documentElement.classList.contains('full')+' rot:'+document.documentElement.classList.contains('rot')")
        shot('0cover')
        page.click('#logoT'); page.wait_for_timeout(200)
        res['share'] = page.evaluate("(()=>{const r=document.querySelector('.sbox').getBoundingClientRect();return {rect:[r.left,r.top,r.right,r.bottom].map(Math.round),off:r.left<-1||r.top<-1||r.right>innerWidth+1||r.bottom>innerHeight+1}})()")
        shot('0share')
        page.click('#shClose'); page.wait_for_timeout(100)
        for g in ['kb', 'oth', 'ws', 'sdk', 'rem']:
            page.click(f'.card[data-g="{g}"]')
            page.wait_for_timeout(1300 if g in ('sdk', 'ws') else 900)
            f = game_frame(page)
            close_panel(f)
            if g == 'rem':
                # get to your turn (skip the doubles phase)
                for _ in range(40):
                    ph = f.evaluate("__remi.G.phase")
                    if ph == 'dbl':
                        f.evaluate("[...document.querySelectorAll('#acts button')].find(b=>b.textContent==='Play').click()")
                    elif ph in ('draw', 'play'):
                        break
                    page.wait_for_timeout(300)
            res[g] = f.evaluate(MEAS); shot(g + '1')
            f.click('#bRules'); page.wait_for_timeout(150)
            res[g + ' rules'] = f.evaluate(MEAS); shot(g + '2rules')
            f.click('#bSet'); page.wait_for_timeout(150)
            res[g + ' settings'] = f.evaluate(MEAS); shot(g + '3set')
            f.click('#bSet'); page.wait_for_timeout(100)
            if g in STRESS:
                for hn in ([15, 26, 38] if g == 'rem' else [0]):
                    f.evaluate(STRESS[g].replace('HN', str(hn)))
                    if g == 'rem':
                        f.evaluate("[...document.querySelectorAll('#acts button')].find(b=>b.textContent==='Sort').click()")
                    page.wait_for_timeout(250)
                    res[f'{g} stress{hn or ""}'] = f.evaluate(MEAS); shot(f'{g}4stress{hn or ""}')
                    if g == 'rem':
                        res[f'{g} stress{hn}']['table'] = f.evaluate("(()=>{const t=document.getElementById('table'),r=document.getElementById('rack'),b=document.getElementById('bar'),a=document.getElementById('acts'),y=e=>{let v=0;while(e&&e.id!=='app'){v+=e.offsetTop;e=e.offsetParent}return v};return {tableH:t.clientHeight,tableScroll:t.scrollHeight,rackH:r.offsetHeight,rackScroll:r.scrollHeight>r.clientHeight+1,actsBelowBar:y(a)+a.offsetHeight>y(b)+1}})()")
            if g in ('kb', 'oth'):
                f.evaluate("mode='2p';document.body.classList.add('flip');start()")
                page.wait_for_timeout(300)
                res[g + ' flip'] = f.evaluate(MEAS); shot(g + '5flip')
                f.evaluate("mode='cpu';document.body.classList.remove('flip');start()")
            if g == 'rem':
                f.click('#bSet'); page.wait_for_timeout(100)
                f.evaluate("document.querySelectorAll('#sSkin button')[1].click()"); page.wait_for_timeout(300)
                res['rem medias settings'] = f.evaluate(MEAS); shot('rem6medias_set')
                f.click('#bSet'); page.wait_for_timeout(150)
                res['rem medias'] = f.evaluate(MEAS); shot('rem6medias')
                f.click('#bSet'); page.wait_for_timeout(100)
                f.evaluate("document.querySelectorAll('#sLay button')[1].click()"); page.wait_for_timeout(400)
                f.evaluate(STRESS['rem'].replace('HN','15')); f.evaluate("[...document.querySelectorAll('#acts button')].find(b=>b.textContent==='Sort').click()"); page.wait_for_timeout(250)
                res['rem land'] = f.evaluate(MEAS); shot('rem7land')
                res['rem land']['table'] = f.evaluate("(()=>{const t=document.getElementById('table'),r=document.getElementById('rack');return {tableH:t.clientHeight,tableScroll:t.scrollHeight,rackH:r.offsetHeight,rackScroll:r.scrollHeight>r.clientHeight+1}})()")
                f.click('#bSet'); page.wait_for_timeout(150)
                res['rem land settings'] = f.evaluate(MEAS); shot('rem7land_set')
                f.click('#bRules'); page.wait_for_timeout(150)
                res['rem land rules'] = f.evaluate(MEAS)
                f.click('#bRules'); page.wait_for_timeout(100)
            page.evaluate("kbShowCover()"); page.wait_for_timeout(350)
        res['errors'] = errs
        json.dump(res, open(f'{SHOTS}/{name}.json', 'w'))
        # summary line
        print('==', name, 'k cover', res['cover']['k'], res['cover']['full'], '| errors', len(errs), errs[:2])
        for k_, v in res.items():
            if not isinstance(v, dict):
                continue
            issues = []
            for key in ('offscreen', 'outstage', 'overlap'):
                if v.get(key) and not (' rules' in k_ and key != 'overlap'):   # text inside a scrolling Rules panel
                    issues.append(f'{key}={v[key]}')
            if v.get('clip'):
                issues.append(f"clip={v['clip']}")
            p = v.get('panel')
            if p and (p['off'] or p['rows'] or (p['scrolls'] and k_ not in ('sdk rules', 'rem rules', 'rem land rules'))):
                issues.append(f"panel={p}")
            if v.get('off'):
                issues.append(f'share off {v}')
            t = v.get('table')
            if t and (t.get('actsBelowBar') or (k_ == 'rem land' and t['tableH'] < 150)):
                issues.append(f"table={t}")
            if issues:
                total += len(issues)
                print('  ', k_, '|', ' ; '.join(issues))
        total += len(errs)
        ctx.close()
        sys.stdout.flush()
    br.close(); pw.stop()
    print('problems:', total)


if __name__ == '__main__':
    run(sys.argv[1:] or list(DEV))
