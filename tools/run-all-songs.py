import json
from playwright.sync_api import sync_playwright
PRESS = """() => { const S = window.__qk.state(); const t = document.querySelector('.key.target'); if (t) { t.dispatchEvent(new PointerEvent('pointerdown', {bubbles:true})); return 1; } if (S.view==='song' && S.lineDone) { document.querySelector('[data-act="next-line"]').click(); return 2; } return 0; }"""
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1194,'height':834})
    errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.add_init_script("const _st = window.setTimeout; window.setTimeout = (f, ms, ...a) => _st(f, (ms||0)/25, ...a);")
    pg.goto('file://' + __import__('os').path.abspath('www/index.html') + '')
    pg.evaluate("() => document.querySelector('[data-act=songs]').click()")
    names=pg.evaluate("() => [...document.querySelectorAll('[data-act=song]')].map(b=>[b.dataset.i,b.firstChild.textContent])")
    duets=pg.evaluate("() => [...new Set([...document.querySelectorAll('[data-act=duet-open]')].map(b=>b.dataset.name))]")
    dbad=[]
    for name in duets:
        pg.evaluate("() => { if(!document.querySelector('[data-act=songs]')) document.getElementById('homeBtn').click(); document.querySelector('[data-act=songs]').click(); }")
        pg.evaluate("(n) => [...document.querySelectorAll('[data-act=duet-open]')].find(b=>b.dataset.name===n).click()", name)
        ok=False
        for step in range(900):
            if pg.evaluate("() => window.__qk.state().view")=='done': ok=True; break
            pg.evaluate("() => document.querySelectorAll('.key.target').forEach(k=>k.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true})))"); pg.wait_for_timeout(8)
        if not ok: dbad.append(name)
        pg.evaluate("() => document.querySelector('[data-act=again]').click()")
        again=pg.evaluate("() => window.__qk.state().view")
        if again!='duet': dbad.append(name+' again->'+again)
        pg.evaluate("() => document.getElementById('homeBtn').click()")
    print('two-hand pieces', len(duets), 'stuck', dbad)
    bad=[]
    for i,name in names:
        for hands in ('right','both'):
            pg.evaluate("() => { if(!document.querySelector('[data-act=songs]')) document.getElementById('homeBtn').click(); document.querySelector('[data-act=songs]').click(); }")
            pg.evaluate("(i) => document.querySelector('[data-act=song][data-i=\"'+i+'\"]').click()", i)
            for _ in range(4):
                if hands in pg.evaluate("() => document.querySelector('[data-act=hands]').textContent"): break
                pg.evaluate("() => document.querySelector('[data-act=hands]').click()")
            ok=False
            for step in range(600):
                if pg.evaluate("() => window.__qk.state().view")=='done': ok=True; break
                pg.evaluate(PRESS); pg.wait_for_timeout(8)
            if not ok: bad.append(name+'/'+hands)
            pg.evaluate("() => document.querySelector('[data-act=home]').click()")
    print('songs', len(names), 'stuck', bad, 'errors', errs[:5]); b.close()
