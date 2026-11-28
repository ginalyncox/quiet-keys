from playwright.sync_api import sync_playwright
src=open('tools/run-all-lessons.py').read()
SPEED=src.split('SPEED = """')[1].split('"""')[0]
PRESS=src.split('PRESS = """')[1].split('"""')[0]
URL='file://' + __import__('os').path.abspath('www/index.html')
errs=[]; out=[]
ST="() => { const S = window.__qk.state(); return {view:S.view, line:S.line, pos:S.pos, busy:!!S.busy, done:!!S.lineDone, msg:S.msg, spot:S.spot ? {at:S.spot.at, n:S.spot.stages.length, say:S.spot.stages[S.spot.at].say, hand:S.spot.stages[S.spot.at].hand||null, slip:S.spot.slip} : null}; }"
def open_piece(pg, name):
    pg.evaluate("() => { if(!document.querySelector('[data-act=songs]')) document.getElementById('homeBtn').click(); document.querySelector('[data-act=songs]').click(); }")
    pg.evaluate("(n) => [...document.querySelectorAll('.rowbtn')].find(b => b.firstChild.textContent === n).click()", name)
    if pg.query_selector('[data-act=top]'): pg.click('[data-act=top]')
def ready(pg):
    for i in range(4000):
        s=pg.evaluate(ST)
        if not s['spot'] or (not s['busy'] and not s['done']): return s
        pg.wait_for_timeout(10)
    raise SystemExit('never ready')
def one_pass(pg):
    """play the current round once; returns state after the pass settles"""
    s=ready(pg); at=s['spot']['at']
    for i in range(3000):
        s=pg.evaluate(ST)
        if not s['spot'] or s['done']: break
        if s['busy']: pg.wait_for_timeout(10); continue
        pg.evaluate(PRESS); pg.wait_for_timeout(8)
    return ready(pg)
def wrong(pg):
    pg.evaluate("() => { const k=[...document.querySelectorAll('.oct.on .key')].find(k => !k.classList.contains('target') && !k.classList.contains('held')); k.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true})); }")
with sync_playwright() as p:
    b=p.chromium.launch()
    for vp in [{'width':390,'height':780},{'width':1194,'height':834}]:
        pg=b.new_page(viewport=vp); pg.on('pageerror', lambda e: errs.append(str(e))); pg.add_init_script(SPEED); pg.goto(URL)
        # --- a melody: three rounds, same line, never moves on by itself ---
        open_piece(pg, "Greensleeves (whole song)")
        pg.evaluate(PRESS); pg.evaluate(PRESS)                      # partway into line 1
        pg.click('[data-act=spot]'); s=ready(pg); out.append((vp['width'],'song start',s)); assert s['spot']['n']==3 and s['spot']['at']==0 and s['pos']==0
        assert pg.query_selector('[data-act=spot-off]') and not pg.query_selector('[data-act=along]') and not pg.query_selector('[data-act=next-line]')
        says=[]
        # a slip keeps the same round
        wrong(pg); s=pg.evaluate(ST); assert s['spot']['slip'], s
        s=one_pass(pg); out.append(('after slip pass',s)); assert s['spot']['at']==0 and s['pos']==0 and not s['spot']['slip']
        for k in range(3):
            says.append(pg.evaluate(ST)['spot']['say']); s=one_pass(pg)
        out.append(('song end',s,says)); assert s['spot'] is None and s['line']==0 and s['done'] and 'smoother' in s['msg']
        assert pg.query_selector('[data-act=next-line]') and pg.query_selector('[data-act=line-again]')
        # hear again, then leave
        pg.click('[data-act=line-again]'); pg.click('[data-act=spot]'); ready(pg); pg.click('[data-act=spot-hear]'); assert pg.evaluate(ST)['busy']; ready(pg)
        pg.click('[data-act=spot-off]'); s=pg.evaluate(ST); assert s['spot'] is None and s['pos']==0 and not s['busy'] and pg.query_selector('[data-act=along]')
        # leaving while it is still playing the line
        pg.click('[data-act=spot]'); assert pg.evaluate(ST)['busy']; pg.click('[data-act=spot-off]'); pg.wait_for_timeout(200); s=pg.evaluate(ST); assert s['spot'] is None and not s['busy'], s
        # --- two hands: right alone, left alone, together, together quicker ---
        open_piece(pg, "Far Light (two hands)")
        pg.click('[data-act=spot]'); s=ready(pg); assert s['spot']['n']==4 and s['spot']['hand']=='r'
        lanes=pg.evaluate("() => [...document.querySelectorAll('.duet .lane')].map(l => l.querySelectorAll('.chip').length)"); out.append(('right alone lanes',lanes)); assert lanes[0]>0 and lanes[1]==0
        hands=[]
        for k in range(4):
            st=pg.evaluate(ST)['spot']; hands.append(st['hand']); 
            tg=pg.evaluate("() => document.querySelectorAll('.key.target').length"); 
            s=one_pass(pg)
        out.append(('duet end',s,hands)); assert hands==['r','l',None,None] and s['spot'] is None and s['line']==0 and s['done']
        assert pg.query_selector('[data-act=d-next]')
        # full line is back
        pg.click('[data-act=d-again]'); lanes=pg.evaluate("() => [...document.querySelectorAll('.duet .lane')].map(l => l.querySelectorAll('.chip').length)"); assert lanes[0]>0 and lanes[1]>0
        # --- a line where one hand rests: two rounds only ---
        open_piece(pg, "Moonlight Sonata, whole first movement (two hands)")
        pg.click('[data-act=spot]'); s=ready(pg); out.append(('moonlight line 1',s['spot'])); assert s['spot']['n']==2 and s['spot']['hand'] is None
        s=one_pass(pg); s=one_pass(pg); assert s['spot'] is None and s['line']==0
        # leaving by Home, then the piece opens normally
        pg.click('[data-act=d-again]'); pg.click('[data-act=spot]'); pg.evaluate("() => document.getElementById('homeBtn').click()"); pg.wait_for_timeout(200)
        open_piece(pg, "Far Light (two hands)"); s=pg.evaluate(ST); assert s['spot'] is None and s['view']=='duet'
        # inside a lesson song too
        assert pg.evaluate("() => document.documentElement.scrollWidth <= window.innerWidth + 1")
        pg.close()
    b.close()
for o in out: print(o)
print('ERRORS', errs)
