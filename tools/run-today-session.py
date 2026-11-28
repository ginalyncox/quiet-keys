import sys
from playwright.sync_api import sync_playwright
src=open('tools/run-all-lessons.py').read()
SPEED=src.split('SPEED = """')[1].split('"""')[0]
PRESS=src.split('PRESS = """')[1].split('"""')[0]
errs=[]; out=[]
def play(pg, limit=4000):
    for i in range(limit):
        v=pg.evaluate("() => window.__qk.state().view")
        if v=='done': return True
        pg.evaluate(PRESS); pg.wait_for_timeout(12)
    return False
with sync_playwright() as p:
    b=p.chromium.launch()
    pg=b.new_page(viewport={'width':390,'height':780})
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.add_init_script(SPEED)
    pg.goto('file://' + __import__('os').path.abspath('www/index.html'))
    # 1. fresh user: Today = one new lesson only
    out.append(('home slab', pg.inner_text('[data-act=today]')))
    pg.click('[data-act=today]')
    out.append(('fresh steps', pg.evaluate("() => window.__qk.today().steps.length")))
    assert play(pg); st=pg.evaluate("() => window.__qk.state().session"); out.append(('fresh end', st, pg.inner_text('h1')))
    assert st=='end'
    pg.click('[data-act=home]')
    out.append(('home after', pg.inner_text('[data-act=today]')))
    # 2. "A little more": new + review (lesson review, no songs yet)
    pg.click('[data-act=today]')
    steps=pg.evaluate("() => window.__qk.today().steps.map(s => s.L ? s.L.id : 's:'+(s.song||s.piece).name)"); out.append(('second steps', steps))
    assert len(steps)==2 and steps[0]!=steps[1]
    assert play(pg); out.append(('mid', pg.evaluate("() => window.__qk.state().session"), pg.inner_text('#stage')[:120].replace('\n',' | ')))
    assert pg.evaluate("() => window.__qk.state().session")=='mid'
    pg.click('[data-act=today-next]')
    assert play(pg); out.append(('end', pg.evaluate("() => window.__qk.state().session"), pg.inner_text('#stage')[:90].replace('\n',' | ')))
    assert pg.evaluate("() => window.__qk.state().session")=='end'
    # 3. leaving mid-session cancels quietly
    pg.click('[data-act=today]'); pg.wait_for_timeout(30); pg.evaluate("() => document.getElementById('homeBtn').click()")
    out.append(('cancel', pg.evaluate("() => window.__qk.today()")))
    assert pg.evaluate("() => window.__qk.today()") is None
    # 4. song review is preferred and rotates; all-done user gets two reviews
    pg.evaluate("""() => { const s = JSON.parse(localStorage.getItem('quiet-keys')); s.songs = {'Ode to Joy':true,'Greensleeves':true,'Moonlight Sonata (opening)':true}; s.seen = {'s:Ode to Joy':5,'s:Greensleeves':1,'s:Moonlight Sonata (opening)':9}; localStorage.setItem('quiet-keys', JSON.stringify(s)); }""")
    pg.reload(); pg.click('[data-act=today]')
    steps=pg.evaluate("() => window.__qk.today().steps.map(s => s.L ? s.L.id : 's:'+(s.song||s.piece).name)"); out.append(('song review', steps))
    assert steps[1]=='s:Greensleeves'
    pg.evaluate("() => document.getElementById('homeBtn').click()")
    ids=pg.evaluate("() => { document.querySelector('[data-act=lessons]').click(); return [...document.querySelectorAll('[data-act=lesson]')].map(b=>b.dataset.id); }")
    pg.evaluate("(ids) => { const s = JSON.parse(localStorage.getItem('quiet-keys')); ids.forEach(i => s.done[i]=true); localStorage.setItem('quiet-keys', JSON.stringify(s)); }", ids)
    pg.reload(); out.append(('all done slab', pg.inner_text('[data-act=today]')))
    pg.click('[data-act=today]')
    steps=pg.evaluate("() => window.__qk.today().steps.map(s => s.L ? s.L.id : 's:'+(s.song||s.piece).name)"); out.append(('all-done steps', steps))
    assert len(steps)==2 and steps[0]!=steps[1]
    # 5. old save without seen/day still loads
    pg.evaluate("() => localStorage.setItem('quiet-keys', JSON.stringify({done:{'L0-0':true}, songs:{}, hands:'right'}))")
    pg.reload(); out.append(('old save slab', pg.inner_text('[data-act=today]')))
    b.close()
for o in out: print(o)
print('ERRORS', errs)
