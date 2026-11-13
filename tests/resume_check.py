"""Saved games: make a move in each game, reload, reopen it and check the game came back.

    python3 tests/resume_check.py

Knucklebones (also during the CPU's turn), Othello, Water Sort, Sudoku; also that a finished Knucklebones game
adds to the saved record and starts fresh. Remi has its own checks in remi_check.py. iPhone 12 simulation.
"""
from harness import start_server, open_page, open_game, to_cover
import harness; harness.strict()   # a printed False ends the script with exit code 1

port = start_server(8833)
pw, b, page = open_page(port, 'iphone12')


def reopen(g):
    page.reload(); page.wait_for_timeout(800)
    return open_game(page, g, 1200)


ls = lambda f, k: f.evaluate(f"localStorage.getItem('{k}')")

f = open_game(page, 'kb')
f.evaluate("document.querySelector('#pg .col.can').click()"); page.wait_for_timeout(2500)
a = f.evaluate("JSON.stringify([p,c,turn])"); f = reopen('kb')
print('Knucklebones resume:', a == f.evaluate("JSON.stringify([p,c,turn])"), '|', f.evaluate("document.querySelector('#msg .t').textContent"))
f.evaluate("document.querySelector('#pg .col.can').click()"); page.wait_for_timeout(300); f = reopen('kb'); page.wait_for_timeout(2500)
print('Knucklebones reopened during the CPU turn, CPU finished and it is your turn:', f.evaluate("turn") == 'p')
rec0 = ls(f, 'kb-rec')
for i in range(60):
    if f.evaluate("over"): break
    if f.evaluate("turn==='p'"): f.evaluate("document.querySelector('#pg .col.can')&&document.querySelector('#pg .col.can').click()")
    page.wait_for_timeout(1600)
print('Knucklebones record:', rec0, '->', ls(f, 'kb-rec'))
f = reopen('kb'); print('Knucklebones finished game starts fresh:', f.evaluate("p.flat().length+c.flat().length") == 0)
to_cover(page)

f = open_game(page, 'oth')
f.evaluate("document.querySelector('#board button:not([disabled])').click()"); page.wait_for_timeout(1800)
a = f.evaluate("JSON.stringify([bd,turn])"); f = reopen('oth')
print('Othello resume:', a == f.evaluate("JSON.stringify([bd,turn])"), '|', f.evaluate("document.querySelector('#msg>div').textContent"))
to_cover(page)

f = open_game(page, 'ws')
t = f.evaluate("[...document.querySelectorAll('#board .tube')].map(t=>t.children.length)")
f.evaluate(f"document.querySelectorAll('#board .tube')[{t.index(4)}].click();document.querySelectorAll('#board .tube')[{t.index(0)}].click()")
page.wait_for_timeout(200); a = ls(f, 'ws_game'); f = reopen('ws')
print('Water Sort resume:', a == ls(f, 'ws_game'), '|', f.evaluate("document.getElementById('msg').textContent"), '|', f.evaluate("document.getElementById('sub').textContent"))
to_cover(page)

f = open_game(page, 'sdk', 1500)
f.evaluate("(()=>{const i=val.findIndex((v,k)=>!giv[k]&&!v);[...document.querySelectorAll('#board button')][i].click();"
           "[...document.querySelectorAll('#pad button')].find(b=>b.textContent.trim()==String(sol[i])).click()})()")
page.wait_for_timeout(1500); a = f.evaluate("JSON.stringify([val,S.diff])"); t0 = f.evaluate("time"); f = reopen('sdk')
print('Sudoku resume:', a == f.evaluate("JSON.stringify([val,S.diff])"), '| clock kept:', t0 > 0 and f.evaluate("time") >= t0 - 300)

print('console errors:', page.errors)
b.close(); pw.stop()
