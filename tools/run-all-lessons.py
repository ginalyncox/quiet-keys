import sys, json
from playwright.sync_api import sync_playwright
SPEED = """
const _st = window.setTimeout; window.setTimeout = (f, ms, ...a) => _st(f, (ms||0)/25, ...a);
"""
PRESS = """
() => {
  const S = window.__qk.state();
  const t = [...document.querySelectorAll('.key.target')];
  if (t.length) { const k = t[0]; k.dispatchEvent(new PointerEvent('pointerdown', {bubbles:true})); return 'target'; }
  if (S.busy) return 'busy';
  if (S.view === 'find' || S.view === 'read') { const el = document.querySelector('.key[data-key="'+S.target.key+'"][data-oct="'+S.target.oct+'"]'); el.dispatchEvent(new PointerEvent('pointerdown', {bubbles:true})); return 'find'; }
  if (S.view === 'echo') { const n = S.seq[S.pos]; document.querySelector('.oct.on .key[data-key="'+n.key+'"]').dispatchEvent(new PointerEvent('pointerdown', {bubbles:true})); return 'echo'; }
  if (S.view === 'song' && S.lineDone) { document.querySelector('[data-act="next-line"]').click(); return 'next'; }
  return S.view;
}
"""
errs=[]
with sync_playwright() as p:
    b=p.chromium.launch()
    for vp,name in [({'width':390,'height':780},'phone'),({'width':1194,'height':834},'ipad')]:
        pg=b.new_page(viewport=vp)
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('console', lambda m: errs.append(m.text) if m.type=='error' and 'fonts' not in m.text and 'ERR_' not in m.text else None)
        pg.add_init_script(SPEED)
        pg.goto('file://' + __import__('os').path.abspath('www/index.html') + '')
        pg.screenshot(path=f'shot-{name}-home.png')
        ids=pg.evaluate("() => { document.querySelector('[data-act=lessons]').click(); return [...document.querySelectorAll('[data-act=lesson]')].map(b=>b.dataset.id+'|'+b.textContent); }")
        pg.screenshot(path=f'shot-{name}-lessons.png')
        bad=[]
        for item in ids:
            lid=item.split('|')[0]
            pg.evaluate("() => document.querySelector('[data-act=lessons]') ? 0 : document.getElementById('homeBtn').click()")
            pg.evaluate("() => document.querySelector('[data-act=lessons]').click()")
            pg.evaluate("(id) => document.querySelector('[data-act=lesson][data-id=\"'+id+'\"]').click()", lid)
            ok=False
            for step in range(900):
                v=pg.evaluate("() => window.__qk.state().view")
                if v=='done': ok=True; break
                r=pg.evaluate(PRESS)
                pg.wait_for_timeout(12 if r!='busy' else 30)
            if not ok: bad.append(item+' -> stuck at '+json.dumps(pg.evaluate("() => { const S=window.__qk.state(); return {v:S.view, r:S.round, busy:S.busy, line:S.line, pos:S.pos, msg:S.msg}; }")))
            pg.evaluate("() => document.querySelector('[data-act=home]').click()")
        print(name, 'lessons', len(ids), 'stuck', bad)
        pg.close()
    b.close()
print('errors', errs[:10])
