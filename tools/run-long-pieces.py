from playwright.sync_api import sync_playwright
src=open('tools/run-all-lessons.py').read()
SPEED=src.split('SPEED = """')[1].split('"""')[0]
PRESS=src.split('PRESS = """')[1].split('"""')[0]
errs=[]; out=[]
URL='file://' + __import__('os').path.abspath('www/index.html')
def step(pg): pg.evaluate(PRESS); pg.wait_for_timeout(10)
def open_piece(pg, name):
    pg.evaluate("() => { if(!document.querySelector('[data-act=songs]')) document.getElementById('homeBtn').click(); document.querySelector('[data-act=songs]').click(); }")
    pg.evaluate("(n) => [...document.querySelectorAll('.rowbtn')].find(b => b.firstChild.textContent === n).click()", name)
with sync_playwright() as p:
    b=p.chromium.launch()
    for vp in [{'width':390,'height':780},{'width':1194,'height':834}]:
        pg=b.new_page(viewport=vp); pg.on('pageerror', lambda e: errs.append(str(e))); pg.add_init_script(SPEED); pg.goto(URL)
        pg.evaluate("() => { const s = JSON.parse(localStorage.getItem('quiet-keys')||'{}'); s.auto = false; localStorage.setItem('quiet-keys', JSON.stringify(s)); }"); pg.reload()
        for name in ["Greensleeves (whole song)", "Prelude in C (whole piece)", "Minuet in G (whole piece)", "Minuet in G, whole piece (two hands)", "Gymnop\u00e9die No. 1, whole piece (two hands)", "F\u00fcr Elise, main part (two hands)"]:
            open_piece(pg, name)
            st=pg.evaluate("() => { const S = window.__qk.state(); return [S.view, (S.song||S.piece).lines.length, S.line]; }"); out.append((vp['width'], name, st))
            # play to line 5, leave, come back
            for i in range(3000):
                if pg.evaluate("() => window.__qk.state().line") >= 5: break
                step(pg)
            pg.evaluate("() => document.getElementById('homeBtn').click()")
            open_piece(pg, name)
            ln=pg.evaluate("() => window.__qk.state().line"); out.append(('resume line', ln, 'note' if pg.query_selector('[data-act=top]') else 'NO NOTE')); assert ln==5
            pg.click('[data-act=top]'); assert pg.evaluate("() => window.__qk.state().line")==0
            pg.evaluate("() => document.getElementById('homeBtn').click()"); open_piece(pg, name); assert pg.evaluate("() => window.__qk.state().line")==0, 'start from the top must be remembered'
            # play all the way through
            for i in range(20000):
                if pg.evaluate("() => window.__qk.state().view")=='done': break
                step(pg)
            v=pg.evaluate("() => window.__qk.state().view"); out.append(('finished', v)); assert v=='done'
            pg.evaluate("() => document.getElementById('homeBtn').click()")
            open_piece(pg, name); assert pg.evaluate("() => window.__qk.state().line")==0
            assert pg.evaluate("() => document.documentElement.scrollWidth <= window.innerWidth + 1")
        # both-hands mode on the melody version completes too
        for bname in ["Minuet in G (whole piece)", "Greensleeves (whole song)", "Prelude in C (whole piece)"]:
            open_piece(pg, bname)
            if pg.query_selector("[data-act=top]"): pg.click("[data-act=top]")
            for k in range(3):
                if 'oth' in pg.inner_text('[data-act=hands]'): break
                pg.click('[data-act=hands]')
            out.append(('hands', bname, pg.inner_text('[data-act=hands]')))
            for i in range(20000):
                if pg.evaluate("() => window.__qk.state().view")=='done': break
                step(pg)
            assert pg.evaluate("() => window.__qk.state().view")=='done', bname
            pg.evaluate("() => document.getElementById('homeBtn').click()")
        pg.close()
    b.close()
for o in out: print(o)
print('ERRORS', errs)
