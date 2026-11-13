"""What every game gets from the shared core (games/core.js, core.css), checked in each of the five:

- Rules open by themselves the first time only; Rules / Settings toggle, show the x while open, close on Escape
- a tap outside the open panel closes it and does nothing else in the game
- Sound and Scanlines: set in one game, all five follow; a game that isn't on screen is quiet; both reset when the app reopens
- the red button asks "Tap again", goes back by itself after 3 s, and acts on the second tap
- Exit closes an open panel and shows the cover; Remi forgets Medias on Exit and on the Back button

    python3 tests/core_check.py        # exit code 1 if anything fails
"""
import sys
from harness import start_server, open_page, open_game, game_frame, to_cover

port = start_server(8847)
GAMES = ['kb', 'oth', 'ws', 'sdk', 'rem']
SEEN = {'kb': 'kb-rules-seen', 'oth': 'oth-rules-seen', 'ws': 'ws-rules-seen', 'sdk': 'sdk-rules-seen', 'rem': 'remi-rules-seen'}
RED = {'kb': 'btnCancel', 'oth': 'btnCancel', 'ws': 'btnReset', 'sdk': 'btnCancel', 'rem': 'btnNew'}
# something tappable in the play area, and what must not change when it is tapped with a panel open
TAP = {'kb': ('.side.you .col.can', "JSON.stringify(p)"), 'oth': ('#board .sq.can', "JSON.stringify(bd)"), 'ws': ('.tube', "document.querySelectorAll('.tube.sel,.tube.pick,.tube[aria-pressed=true]').length"),
       'sdk': ('#board .c', "String(sel)"), 'rem': ('#rack .tl', "document.querySelectorAll('#rack .tl.sel').length")}
fails = []


def ok(name, cond, extra=''):
    print(('  ok   ' if cond else '  FAIL ') + name, '' if cond else extra)
    if not cond:
        fails.append(name)


def state(f):
    return f.evaluate("({open:document.getElementById('panel').hidden?'':document.getElementById('panel').dataset.p,r:document.getElementById('bRules').getAttribute('aria-expanded'),s:document.getElementById('bSet').getAttribute('aria-expanded')})")


def sw(f):
    return f.evaluate("[document.getElementById('tgSound').textContent,document.getElementById('tgCrt').textContent,sndOn,document.body.classList.contains('nocrt')].join()")


def remi_to_turn(page, f):
    for _ in range(40):
        ph = f.evaluate("__remi.G.phase")
        if ph == 'dbl':
            f.evaluate("[...document.querySelectorAll('#acts button')].find(b=>b.textContent==='Play').click()")
        elif ph in ('draw', 'play'):
            return
        page.wait_for_timeout(300)


pw, b, page = open_page(port, 'iphone12')
print('## first visit, panel, outside tap, Escape, red button')
for g in GAMES:
    page.click(f'.card[data-g="{g}"]'); page.wait_for_timeout(1300); f = game_frame(page)      # (open_game would close the Rules)
    ok(g + ' Rules open by themselves the first time', state(f)['open'] == 'rules' and page.evaluate("(k)=>localStorage.getItem(k)", SEEN[g]) == '1')
    f.click('#bRules'); ok(g + ' Rules button closes them', state(f) == {'open': '', 'r': 'false', 's': 'false'})
    if g == 'rem':
        remi_to_turn(page, f)
    f.click('#bSet'); ok(g + ' Settings open', state(f) == {'open': 'settings', 'r': 'false', 's': 'true'})
    ok(g + ' open button shows the x', 'Settings ×' in f.evaluate("getComputedStyle(document.getElementById('bSet'),'::after').content+''") or f.evaluate("getComputedStyle(document.getElementById('bSet'),'::after').content").strip('"').strip() == '×')
    f.click('#bRules'); ok(g + ' Rules replace Settings', state(f) == {'open': 'rules', 'r': 'true', 's': 'false'})
    sel, expr = TAP[g]
    before = f.evaluate(expr)
    f.evaluate("(s)=>document.querySelector(s).click()", sel); page.wait_for_timeout(150)
    ok(g + ' outside tap closes the panel and does nothing else', state(f)['open'] == '' and f.evaluate(expr) == before)
    f.click('#bSet'); page.keyboard.press('Escape'); page.wait_for_timeout(80)
    ok(g + ' Escape closes the panel', state(f)['open'] == '')
    # red button
    if g in ('kb', 'oth'):
        f.evaluate("(s)=>document.querySelector(s).click()", sel); page.wait_for_timeout(2600)
    elif g == 'sdk':
        f.evaluate("(()=>{const i=val.findIndex(v=>!v);cells[i].click();keys[sol[i]].click()})()")
    elif g == 'rem':
        f.evaluate("__remi.G.tn=5")
    f.click('#bSet'); page.wait_for_timeout(100)
    red = '#' + RED[g]; label = f.evaluate("(s)=>document.querySelector(s).textContent", red)
    f.click(red); page.wait_for_timeout(100)
    ok(g + ' red button asks Tap again', f.evaluate("(s)=>{const b=document.querySelector(s);return b.textContent==='Tap again'&&b.classList.contains('arm')}", red) and state(f)['open'] == 'settings')
    page.wait_for_timeout(3200)
    ok(g + ' red button goes back by itself after 3 s', f.evaluate("(s)=>{const b=document.querySelector(s);return b.textContent+'|'+b.classList.contains('arm')}", red) == label + '|false')
    f.click(red); f.click('#bSet'); f.click('#bSet'); page.wait_for_timeout(100)
    ok(g + ' red button is fresh when Settings reopen', f.evaluate("(s)=>{const b=document.querySelector(s);return b.textContent+'|'+b.classList.contains('arm')}", red) == label + '|false')
    f.click(red); f.click(red); page.wait_for_timeout(400)
    ok(g + ' second tap acts and closes Settings', state(f)['open'] == '')
    # Exit with a panel open
    f.click('#bRules'); f.click('#bar .mnu'); page.wait_for_timeout(500)
    ok(g + ' Exit shows the cover and closes the panel', page.evaluate("!document.getElementById('cover').hidden") and state(f)['open'] == '')
page.reload(); page.wait_for_timeout(700)
f = open_game(page, 'kb', 900)
ok('Rules stay closed on later visits', state(f)['open'] == '')
to_cover(page)

print('## Sound and Scanlines')
f = open_game(page, 'oth', 900); to_cover(page)                    # a game already loaded when the change is made
f = open_game(page, 'ws', 1300); f.click('#bSet'); f.click('#tgSound'); f.click('#tgCrt'); page.wait_for_timeout(100)
ok('ws switched: sound on, scanlines off', sw(f) == 'On,Off,true,true')
ok('ws silent loop and audio started by the tap', f.evaluate("!!naKeep&&!!AC"))
to_cover(page)
ok('ws paused when the cover takes over', page.evaluate("[...document.querySelectorAll('iframe')].every(f=>f.contentWindow.naHid()&&(!f.contentWindow.naKeep||f.contentWindow.naKeep.paused))"))
for g in ['oth', 'kb', 'rem', 'sdk']:
    f = open_game(page, g, 1300); f.click('#bSet'); page.wait_for_timeout(100)
    ok(g + ' follows', sw(f) == 'On,Off,true,true', sw(f))
    if g == 'sdk':
        f.click('#tgSound'); f.click('#tgCrt'); page.wait_for_timeout(100)      # switch back from another game
    to_cover(page)
for g in ['ws', 'kb']:
    f = open_game(page, g, 900); f.click('#bSet'); page.wait_for_timeout(100)
    ok(g + ' follows the change back', sw(f) == 'Off,On,false,false', sw(f)); to_cover(page)
f = open_game(page, 'kb', 900); f.click('#bSet'); f.click('#tgSound'); to_cover(page)
page.reload(); page.wait_for_timeout(700)
for g in ['kb', 'rem']:
    f = open_game(page, g, 1000); f.click('#bSet'); page.wait_for_timeout(100)
    ok(g + ' resets when the app reopens', sw(f) == 'Off,On,false,false', sw(f)); to_cover(page)

print('## Remi forgets Medias on every way out')
for way in ['exit', 'back']:
    f = open_game(page, 'rem', 1000); f.click('#bSet'); f.evaluate("document.querySelectorAll('#sSkin button')[1].click()"); page.wait_for_timeout(200)
    f.evaluate("document.querySelectorAll('#sLay button')[1].click()"); page.wait_for_timeout(300)
    ok('Medias Landscape on', f.evaluate("document.documentElement.classList.contains('lnd')"))
    if way == 'exit':
        f.click('#bar .mnu')
    else:
        page.go_back()
    page.wait_for_timeout(600)
    f = open_game(page, 'rem', 800)
    ok(way + ': back to Neon upright', f.evaluate("!document.documentElement.classList.contains('lnd')&&!document.documentElement.classList.contains('sk-m')"))
    to_cover(page)
ok('no console errors', not page.errors, page.errors[:3])
b.close(); pw.stop()
print('failures:', len(fails), fails)
sys.exit(1 if fails else 0)
