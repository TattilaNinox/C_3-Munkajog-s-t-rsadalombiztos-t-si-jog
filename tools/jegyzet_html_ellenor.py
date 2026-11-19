#!/usr/bin/env python3
"""A jegyzet-HTML (termekek/jegyzet_html/, tools/jegyzet_html.py) ellenőrzése.   python3 tools/jegyzet_html_ellenor.py

Tételenként:
  - a HTML jól formált (html.parser; nyitó és záró címkék párban), csak az engedett elemek, osztályok és stílusok
    szerepelnek, és csak az engedett helyen (a doboz belseje, a lista elemei, a <h1> csak egyrészes tétel elején);
  - a HTML-ből visszaszedett szöveg sorrendben, pontosan egyszer adja a tétel minden blokkját (tools/tetel_blokk.py):
    főcím = <h2>, alcím = <h3> (mondatkezdő írással: jegyzet_html.cimsor; a betűméreten kívül azonos a tételszöveggel), bekezdés = <p> vagy <li>, doboz = cimke + sorok; a doboz cimkéje és sorai betűre
    egyeznek a tétel dobozával (a fejléc utáni sorok a következő blokkig; ezek eleje a kozos.dobozok sorai – ha a
    tetel_blokk még egy lezáró sort a dobozhoz számít, amelyet a kozos.dobozok nem, az FIGYELEM, nem hiba); a blokkok együtt a tétel minden nem üres sorát adják (a cím kivételével);
  - a részek blokktartománya folytonos, a partIndex 1-től folytonos, a partCount egyezik;
  - minden jegyzetazonosító létezik a bázisban (egyeb/notes), egyedi, a ttsId a jegyzet audioSource-a;
  - a htmlContent = a részek HTML-jének összefűzése; a lenyomatok és az index.json egyeznek.
Az utolsó sor: „jegyzet_html_ellenor: … hibás: N”; hibánál a kilépési kód 1.
"""
import glob, hashlib, html, json, os, re, sys
from html.parser import HTMLParser
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kozos
import tetel_blokk
from jegyzet_html import cimsor

GY = kozos.GYOKER
KI = os.path.join(GY, 'termekek', 'jegyzet_html')
PONT = 'display:block;padding-left:28px'
ALPONT = 'display:block;padding-left:42px'
FELSOROLASJEL = re.compile(r'^[-–•]\s+')
# elem: (engedett szülők, engedett attribútumok {név: engedett értékek})
ENGEDETT = {
    'h1': ({None}, {}), 'h2': ({None}, {}), 'h3': ({None}, {}), 'p': ({None, 'div'}, {}), 'ul': ({None}, {}),
    'li': ({'ul'}, {}), 'div': ({None}, {'class': {'jogszabaly-doboz'}}), 'br': ({'p'}, {}),
    'span': ({'div', 'p'}, {'class': {'jogszabaly-cimke', 'jogszabaly-pont', 'jogszabaly-alpont'}, 'style': {PONT, ALPONT}}),
}
SPAN_STILUS = {'jogszabaly-cimke': None, 'jogszabaly-pont': PONT, 'jogszabaly-alpont': ALPONT}


class Bont(HTMLParser):
    """A HTML → elemsor: ('h1'|'h2'|'h3'|'p'|'li', szöveg) és ('d', cimke, [sorok])."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.verem = []; self.hibak = []; self.elemek = []; self.buf = None; self.doboz = None; self.sor = None

    def handle_starttag(self, t, a):
        szulo = self.verem[-1][0] if self.verem else None
        if t not in ENGEDETT:
            self.hibak.append(f'nem engedett elem: <{t}>')
        else:
            sz, attr = ENGEDETT[t]
            if szulo not in sz:
                self.hibak.append(f'<{t}> nem engedett helyen (szülő: {szulo})')
            for k, v in a:
                if k not in attr or v not in attr[k]:
                    self.hibak.append(f'<{t}> nem engedett attribútum: {k}="{v}"')
            ad = dict(a)
            if t == 'span':
                c = ad.get('class')
                if SPAN_STILUS.get(c) != ad.get('style'):
                    self.hibak.append(f'<span class="{c}"> stílusa nem a szabályos: {ad.get("style")}')
                if c == 'jogszabaly-cimke' and szulo != 'div':
                    self.hibak.append('a cimke nem a doboz közvetlen eleme')
                if c != 'jogszabaly-cimke' and szulo != 'p':
                    self.hibak.append('pont-span a doboz <p>-jén kívül')
        if t == 'br':
            if self.doboz is None:
                self.hibak.append('<br> a dobozon kívül')
            else:
                self.sor_zar()
            return
        if t == 'div':
            self.doboz = {'cimke': None, 'sorok': [], 'p': 0}
        elif t == 'span' and self.doboz is None:
            self.hibak.append('<span> a dobozon kívül')
        elif t == 'span' and dict(a).get('class') == 'jogszabaly-cimke':
            self.buf = []
        elif t == 'span':
            self.sor_zar(); self.sor = []
        elif t == 'p' and self.doboz is not None:
            self.doboz['p'] += 1; self.sor = []
        elif t in ('h1', 'h2', 'h3', 'p', 'li'):
            self.buf = []
        self.verem.append((t, dict(a)))

    def sor_zar(self):
        if self.sor is not None and self.doboz is not None:
            s = ''.join(self.sor)
            if s:
                self.doboz['sorok'].append(s)
        self.sor = []

    def handle_endtag(self, t):
        if t == 'br':
            return
        if not self.verem or self.verem[-1][0] != t:
            self.hibak.append(f'záró </{t}> nyitott {self.verem[-1][0] if self.verem else "semmi"} helyett'); return
        _, a = self.verem.pop()
        if t == 'div':
            d = self.doboz
            if d['p'] != 1 or d['cimke'] is None:
                self.hibak.append(f'a doboz szerkezete nem cimke + egy <p> ({d["cimke"]})')
            self.elemek.append(('d', d['cimke'], d['sorok'])); self.doboz = None
        elif t == 'span' and self.doboz is None:
            pass
        elif t == 'span' and a.get('class') == 'jogszabaly-cimke':
            self.doboz['cimke'] = ''.join(self.buf); self.buf = None
        elif t == 'span':
            self.sor_zar(); self.sor = []
        elif t == 'p' and self.doboz is not None:
            self.sor_zar(); self.sor = None
        elif t in ('h1', 'h2', 'h3', 'p', 'li'):
            self.elemek.append((t, ''.join(self.buf))); self.buf = None

    def handle_data(self, d):
        if self.sor is not None:
            self.sor.append(d)
        elif self.buf is not None:
            self.buf.append(d)
        elif d.strip():
            self.hibak.append(f'szöveg elemen kívül: {d[:40]!r}')

    def zar(self):
        self.close()
        if self.verem:
            self.hibak.append('nyitva maradt: ' + ', '.join(t for t, _ in self.verem))


def bont(x):
    b = Bont(); b.feed(x); b.zar()
    return b.elemek, b.hibak


def bazis_jegyzetek():
    out = {}
    for f in glob.glob(os.path.join(GY, 'egyeb', 'notes', '*', '*.json')):
        d = json.load(open(f, encoding='utf-8'))
        out[d['id']] = (int(os.path.basename(os.path.dirname(f))), d)
    return out


def main():
    hibak = []; figyelem = []
    H = lambda n, s: hibak.append(f'{n}. tétel: {s}')
    bazis = bazis_jegyzetek()
    ts = kozos.tetelsor()['tetelek']
    latott = {}
    db_resz = db_blokk = 0
    idx = json.load(open(os.path.join(KI, 'index.json'), encoding='utf-8'))
    idx_t = {t['tetel']: t for t in idx['tetelek']}
    for t in ts:
        n = t['sorszam']
        f = os.path.join(KI, f'{n:02d}.json')
        if not os.path.exists(f):
            H(n, 'nincs jegyzet-HTML'); continue
        d = json.load(open(f, encoding='utf-8'))
        if d.get('sema') != 1 or d.get('tetel') != n or d.get('cim') != t['cim']:
            H(n, 'a fej (sema/tetel/cim) hibás')
        txt = kozos.tetel_szoveg(n)
        blokk, ix = tetel_blokk.blokkok_sorral(n)
        dob = kozos.dobozok(txt)
        # a doboz sorai a tétel szövegében: a fejléc utáni nem üres sorok a következő blokkig; eleje = kozos.dobozok
        TL = txt.split('\n'); hatar = ix[1:] + [len(TL)]
        dsor = {}
        for u, b in enumerate(blokk):
            if b[0] == 'd':
                dsor[b[1]] = [l.strip() for l in TL[ix[u] + 1:hatar[u]] if l.strip()]
                k = dob[b[1]][3]
                if dsor[b[1]][:len(k)] != k:
                    H(n, f'a(z) {dob[b[1]][2]} doboz sorai eltérnek a kozos.dobozok soraitól')
                elif len(dsor[b[1]]) > len(k):
                    figyelem.append(f'{n}. tétel {dob[b[1]][2]}: a kozos.dobozok/§-jegyzék {len(dsor[b[1]]) - len(k)} lezáró sort nem tartalmaz (a HTML-ben benne van)')
        # a blokkok együtt a tétel minden nem üres sorát adják
        sorok = []
        for b in blokk:
            sorok += ([dob[b[1]][2]] + dsor[b[1]]) if b[0] == 'd' else [b[1]]
        L = [l.strip() for l in txt.split('\n') if l.strip()][1:]
        elt = [i for i, (x, l) in enumerate(zip(sorok, L)) if x != l and x != FELSOROLASJEL.sub('', l)]
        if len(sorok) != len(L) or elt:
            H(n, f'a blokkok nem a tétel sorai ({len(sorok)}/{len(L)} sor; eltérés: {elt[:3]})')
        reszek = d['reszek']
        if [r['partIndex'] for r in reszek] != list(range(1, len(reszek) + 1)):
            H(n, 'a partIndex nem 1-től folytonos')
        if any(r['partCount'] != len(reszek) for r in reszek):
            H(n, 'a partCount nem egyezik a részek számával')
        # blokktartomány folytonossága
        kov = 0
        for r in reszek:
            a_, b_ = r['blokkok']
            if a_ != kov or b_ < a_:
                H(n, f'{r["partIndex"]}. rész: a blokktartomány nem folytonos ({a_}–{b_}, várt kezdet {kov})')
            kov = b_ + 1
        if kov != len(blokk):
            H(n, f'a részek {kov} blokkot fednek le, a tételben {len(blokk)} van')
        # jegyzetazonosítók
        for r in reszek:
            nid = r['noteId']
            if nid in latott:
                H(n, f'{nid}: a jegyzetazonosító ismétlődik ({latott[nid]}. tétel)')
            latott[nid] = n
            if nid not in bazis:
                H(n, f'{nid}: nincs a bázisban'); continue
            bn, bd = bazis[nid]
            if bn != n or bd.get('type') != 'text' or bd.get('audioSource') != r['ttsId']:
                H(n, f'{nid}: a bázisban más tételé, nem szöveges, vagy a hangforrása ({bd.get("audioSource")}) nem {r["ttsId"]}')
            if len(reszek) > 1 and (bd.get('partIndex'), bd.get('partCount')) != (r['partIndex'], r['partCount']):
                H(n, f'{nid}: a partIndex/partCount eltér a bázistól')
            if hashlib.sha256(r['html'].encode('utf-8')).hexdigest() != r['sha256']:
                H(n, f'{nid}: a lenyomat nem a HTML-é')
        if d['htmlContent'] != ''.join(r['html'] for r in reszek):
            H(n, 'a htmlContent nem a részek összefűzése')
        # a HTML szerkezete és szövege
        vart = []
        for b in blokk:
            if b[0] == 'd':
                vart.append(('d', dob[b[1]][2], dsor[b[1]]))
            elif b[0] in 'fa':
                cs = cimsor(b[1], n)[0]
                if cs.casefold() != b[1].casefold():
                    H(n, f'a címsor mondatkezdő alakja nem csak a betűméretben tér el: {b[1][:60]}')
                vart.append((b[0], cs))
            else:
                vart.append((b[0], b[1]))
        kapott = []
        for r in reszek:
            x = r['html']
            if re.search(r'&(?!amp;|lt;|gt;)', x):
                H(n, f'{r["partIndex"]}. rész: escape-eletlen &')
            if re.search(r'>\s+<|^\s|\s$', x):
                H(n, f'{r["partIndex"]}. rész: szóköz vagy sortörés az elemek között')
            el, hb = bont(x)
            for h in hb:
                H(n, f'{r["partIndex"]}. rész: {h}')
            if len(reszek) == 1:
                if not el or el[0] != ('h1', t['cim']):
                    H(n, 'az egyrészes tétel nem a tétel címével (<h1>) kezdődik')
                el = el[1:]
            if any(e[0] == 'h1' for e in el):
                H(n, f'{r["partIndex"]}. rész: <h1> nem az egyrészes tétel elején')
            db = 0
            for e in el:
                if e[0] == 'd':
                    kapott.append(e)
                else:
                    kapott.append(({'h2': 'f', 'h3': 'a', 'p': 'p', 'li': 'p'}.get(e[0], e[0]), e[1]))
                db += 1
            if db != r['blokkok'][1] - r['blokkok'][0] + 1:
                H(n, f'{r["partIndex"]}. rész: {db} elem, a blokktartomány {r["blokkok"]}')
        if kapott != vart:
            i = next((i for i, (a_, b_) in enumerate(zip(kapott, vart)) if a_ != b_), min(len(kapott), len(vart)))
            H(n, f'a HTML szövege eltér a tétel blokkjaitól a(z) {i}. blokknál: {str(kapott[i] if i < len(kapott) else None)[:120]} ≠ {str(vart[i] if i < len(vart) else None)[:120]}')
        # normalizált összevetés is (a pontos egyezés már magában foglalja; a jelentés kedvéért)
        nk = [kozos.norm(' '.join([e[1]] + e[2]) if e[0] == 'd' else e[1]).casefold() for e in kapott]
        nv = [kozos.norm(' '.join([e[1]] + e[2]) if e[0] == 'd' else e[1]).casefold() for e in vart]
        if nk != nv:
            H(n, 'a normalizált szöveg eltér')
        # index
        it = idx_t.get(n)
        if not it or it['sha256'] != hashlib.sha256(d['htmlContent'].encode('utf-8')).hexdigest() or it['reszek'] != len(reszek) \
                or it['karakter'] != len(d['htmlContent']) or [x['sha256'] for x in it['reszLista']] != [r['sha256'] for r in reszek]:
            H(n, 'az index.json nem egyezik')
        db_resz += len(reszek); db_blokk += len(blokk)
    o = idx['osszesites']
    if o['tetel'] != len(ts) or o['resz'] != db_resz:
        hibak.append(f'index.json összesítés: {o}')
    kanon = json.dumps(idx['tetelek'], ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
    if hashlib.sha256(kanon).hexdigest() != idx['sha256']:
        hibak.append('index.json: a lenyomat nem a tartalomé')
    for h in figyelem:
        print('FIGYELEM', h)
    for h in hibak[:50]:
        print('HIBA', h)
    print(f'jegyzet_html_ellenor: {len(ts)} tétel, {db_resz} rész, {db_blokk} blokk, {o["karakter"]} karakter; hibás: {len(hibak)}')
    sys.exit(1 if hibak else 0)


if __name__ == '__main__':
    main()
