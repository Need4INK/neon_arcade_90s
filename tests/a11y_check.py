"""Accessibility measurements: text contrast and tap-target sizes on the cover and in every game
(game screen, Rules and Settings open), plus colour-blind screenshots of Water Sort and Remi.

    python3 tests/a11y_check.py            # report; pictures in tests/out/a11y_*.png

Contrast is the WCAG ratio of the text colour against the nearest solid background (4.5 wanted for normal text,
3 for large text of 24px+). Tap targets are listed when under 44px (Apple's guideline) in either direction;
WCAG's minimum is 24px. Sizes are for the iPhone 12 layout; on a 320x568 phone everything is 0.71 times that.
"""
import sys
from harness import start_server, open_page, open_game, to_cover, out, GAMES

JS = r"""
() => {
  const BG=[7,3,15];
  const parse=c=>{const m=c.match(/[\d.]+/g).map(Number);return [m[0],m[1],m[2],m.length>3?m[3]:1]};
  const lum=c=>{const f=v=>{v/=255;return v<=.03928?v/12.92:Math.pow((v+.055)/1.055,2.4)};return .2126*f(c[0])+.7152*f(c[1])+.0722*f(c[2])};
  const over=(a,b)=>[0,1,2].map(i=>a[i]*a[3]+b[i]*(1-a[3]));
  const vis=e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e);return r.width>0&&r.height>0&&s.visibility!=='hidden'&&r.bottom>0&&r.top<innerHeight};
  const bgOf=e=>{const st=[];for(let n=e;n&&n.nodeType===1;n=n.parentElement){const c=parse(getComputedStyle(n).backgroundColor);if(c[3]>0){st.push(c);if(c[3]>=1)break}}
    let b=BG;for(let i=st.length-1;i>=0;i--)b=over(st[i],b);return b};
  const op=e=>{let o=1;for(let n=e;n&&n.nodeType===1;n=n.parentElement)o*=parseFloat(getComputedStyle(n).opacity);return o};
  const text=[],seen={};
  document.querySelectorAll('body *').forEach(e=>{
    const t=[...e.childNodes].filter(n=>n.nodeType===3&&n.textContent.trim()).map(n=>n.textContent.trim()).join(' ');
    if(!t||!vis(e))return;
    const s=getComputedStyle(e),bg=bgOf(e),fc=parse(s.color);fc[3]*=op(e);const fg=over(fc,bg);
    const a=lum(fg),b=lum(bg),r=(Math.max(a,b)+.05)/(Math.min(a,b)+.05),px=parseFloat(s.fontSize);
    const need=px>=24?3:4.5;
    if(r<need){const k=s.color+'|'+bg.map(Math.round)+'|'+px+'|'+op(e).toFixed(2);
      if(!seen[k]){seen[k]=1;text.push({ratio:+r.toFixed(2),px,color:s.color,opacity:+op(e).toFixed(2),bg:bg.map(Math.round).join(','),sample:t.slice(0,34)})}}
  });
  const taps=[],ts={};
  document.querySelectorAll('button,a,[role=button],[onclick],.card,.cell,.tube,.tile,.col,td').forEach(e=>{
    if(!vis(e)||getComputedStyle(e).pointerEvents==='none')return;
    const r=e.getBoundingClientRect(),w=Math.round(r.width),h=Math.round(r.height);
    if(w<44||h<44){const k=(e.className||e.tagName)+'|'+w+'x'+h;if(!ts[k]){ts[k]=1;taps.push({w,h,what:(e.tagName.toLowerCase()+(e.id?'#'+e.id:'')+(e.className&&e.className.baseVal===undefined?'.'+String(e.className).trim().split(/\s+/).join('.'):'')).slice(0,40),text:(e.textContent||'').trim().slice(0,16)})}}
  });
  return {text:text.sort((a,b)=>a.ratio-b.ratio),taps:taps.sort((a,b)=>Math.min(a.w,a.h)-Math.min(b.w,b.h))};
}"""


def show(label, r):
    print('\n== ' + label)
    for t in r['text']:
        print('  contrast %-5s %spx %s op %s on rgb(%s)  "%s"' % (t['ratio'], t['px'], t['color'], t['opacity'], t['bg'], t['sample']))
    for t in r['taps']:
        print('  tap %3dx%-3d %s "%s"' % (t['w'], t['h'], t['what'], t['text']))


def bar_btn(f, name):
    f.evaluate("(n)=>{[...document.querySelectorAll('#bar button')].find(b=>b.textContent.trim()===n).click()}", name)
    f.page.wait_for_timeout(350)


if __name__ == '__main__':
    port = start_server(8851)
    pw, browser, page = open_page(port, 'iphone12')
    show('cover', page.evaluate(JS))
    page.click('h1, .title', timeout=2000) if page.query_selector('h1, .title') else None
    page.wait_for_timeout(400); show('cover share pop-up', page.evaluate(JS)); page.keyboard.press('Escape')
    cdp = page.context.new_cdp_session(page)
    for g in GAMES:
        f = open_game(page, g)
        show(g + ' game', f.evaluate(JS))
        if g in ('ws', 'rem'):
            for kind in ['none', 'protanopia', 'deuteranopia', 'tritanopia']:
                cdp.send('Emulation.setEmulatedVisionDeficiency', {'type': kind}); page.wait_for_timeout(250)
                page.screenshot(path=out('a11y_%s_%s.png' % (g, kind)), full_page=True)
            cdp.send('Emulation.setEmulatedVisionDeficiency', {'type': 'none'})
        for name in ('Rules', 'Settings'):
            bar_btn(f, name); show(g + ' ' + name, f.evaluate(JS)); bar_btn(f, name)
        to_cover(page)
    print('\nconsole errors:', page.errors)
    browser.close(); pw.stop()
