#!/usr/bin/env python3
"""S2 – a korpusz hatályossági ellenőrzése (12_tetelsor_szabvany.md, S2; 04_hatalyossag.md).

    python3 tools/hatalyossag.py ujjlenyomat <korpusz-fájl> [--cikk]   # szakaszonkénti ujjlenyomat (az összevetés bemenete)
    python3 tools/hatalyossag.py jelentes                              # jelentesek/hatalyossag.md, korpusz/hatalyok.html, manifest
    python3 tools/hatalyossag.py kapu                                  # 0, ha minden előírt forrás megvan és friss

Az adat a korpusz/allapot.json: forrásonként a megkövetelt jogállapot napján (tetelsor/beallitas.json: jogallapot)
hatályos időállapot, az összevetés eredménye és az eltérő szakaszok. A fájlt az ellenőrzést végző tölti ki; ez a
program nem tölt le semmit, és a korpusz szövegét nem írja át.

Az összevetés módja: a korpusz-fájl szakaszonkénti ujjlenyomatát (ez a program) a hatályos egységes szöveg
oldalán futó tools/hatalyossag/osszevet.js veti össze a megnyitott időállapottal; csak szakaszszámok jönnek vissza.

Csak a standard könyvtárat használja; Python 3.9-től fut.
"""
import html, json, os, re, sys

GY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
K = os.path.join(GY, 'korpusz')
FEJ = re.compile(r'^\s*((?:\d+:)?\d+(?:/[A-Z])?)\.\s*§')
CIKK = re.compile(r'^\s*([A-Z]|[IVXL]+|\d+)\.\s*cikk')
ALLAPOTOK = ('friss', 'elavult', 'hianyzik')


def be(ut):
    return open(os.path.join(GY, ut), encoding='utf-8').read()


def norm(s):
    return re.sub(r'[^0-9a-záéíóöőúüű]', '', s.lower())


def fnv(s):
    h = 0x811c9dc5
    for ch in s:
        h ^= ord(ch)
        h = (h * 0x01000193) & 0xffffffff
    return h


def b36(n, k=4):
    n %= 36 ** k
    jegy, ki = '0123456789abcdefghijklmnopqrstuvwxyz', ''
    for _ in range(k):
        ki = jegy[n % 36] + ki
        n //= 36
    return ki


def szakaszok(fajl, minta=FEJ):
    seg = [['0', []]]
    for sor in open(os.path.join(K, fajl), encoding='utf-8').read().split('\n'):
        m = minta.match(sor)
        if m:
            seg.append([m.group(1), []])
        seg[-1][1].append(sor)
    return [(k, norm(' '.join(v))) for k, v in seg]


def ujjlenyomat(fajl, cikk=False):
    s = szakaszok(fajl, CIKK if cikk else FEJ)
    elso = s[0][1]
    print(','.join(k + '=' + b36(fnv(t)) for k, t in s))
    # a 0. szakasz (cím, preambulum) az oldalon fejléccel bővül: a végéről mért egyezést külön ellenőrizzük
    print('# szakasz: %d; a 0. szakasz hossza %d, a 150. karaktertől vett ujjlenyomata %s'
          % (len(s), len(elso), b36(fnv(elso[150:]), 6)), file=sys.stderr)


# ---------- a tételek és a források kapcsolata ----------
def kulcs(s):
    m = re.match(r'(?:\d+:)?(\d+)(?:/([A-Z]))?', str(s))
    return (int(m.group(1)), m.group(2) or '') if m else None


def tetelek_forrasonkent(ts):
    """fájl -> [(tétel, tól, ig)]"""
    ki = {}
    for t in ts['tetelek']:
        for h in t['hivatkozasok']:
            ki.setdefault(h['fajl'], []).append((t['sorszam'], h.get('tol'), h.get('ig')))
    return ki


def erintett_tetelek(hivok, elteres):
    """Azok a tételek, amelyeknek az előírt tartományába eltérő szakasz esik."""
    ki = {}
    for sorszam, tol, ig in hivok:
        if not elteres:
            continue
        if not tol or kulcs(tol) is None:          # tartomány nélküli előírás: az egész forrás
            ki.setdefault(sorszam, set()).update(elteres)
            continue
        a, b = kulcs(tol), kulcs(ig or tol)
        b = (b[0], b[1] or 'ZZ')                   # a tartomány vége a betűjeles szakaszokat is fedi
        talalat = [e for e in elteres if kulcs(e) and a <= kulcs(e) <= b]
        if talalat:
            ki.setdefault(sorszam, set()).update(talalat)
    return {k: sorted(v, key=kulcs) for k, v in sorted(ki.items())}


def hatarozat_jegyzet(fajl):
    """A bírósági iránymutatás fájljában a Kúria alkalmazhatósági lábjegyzete (a * kezdetű sorok)."""
    sorok = [s for s in open(os.path.join(K, fajl), encoding='utf-8').read().split('\n') if s.startswith('*')]
    return ' '.join(s.lstrip('* ').strip() for s in sorok)


def osszeallit():
    al = json.loads(be('korpusz/allapot.json'))
    ts = json.loads(be('tetelsor/tetelsor.json'))
    hiv = tetelek_forrasonkent(ts)
    atfogo = {a['fajl'] for a in ts.get('atfogoIsmeret', [])}
    hibak = []
    for f in al['forrasok']:
        if f['allapot'] not in ALLAPOTOK:
            hibak.append('%s: ismeretlen állapot: %s' % (f['fajl'], f['allapot']))
        if f['allapot'] != 'hianyzik' and not os.path.exists(os.path.join(K, f['fajl'])):
            hibak.append('%s: nincs ilyen korpusz-fájl' % f['fajl'])
        h = hiv.get(f['fajl'], [])
        f['eloirt'] = bool(h) or f['fajl'] in atfogo or bool(f.get('eloirtTetel'))
        f['tetelek'] = sorted({x[0] for x in h} | set(f.get('eloirtTetel', [])))
        f['erintett'] = erintett_tetelek(h, f.get('elteres', []))
        for t in f.get('eloirtTetel', []):
            f['erintett'].setdefault(t, ['a teljes forrás'])
    # bírósági iránymutatások: minden előírt határozat-fájl, a Kúria lábjegyzetével
    jogszabaly = {f['fajl'] for f in al['forrasok']}
    hat = []
    for fajl in sorted(hiv):
        if fajl in jogszabaly:
            continue
        j = hatarozat_jegyzet(fajl)
        if not j:
            besorolas = 'nincs lábjegyzet'
        elif re.search(r'csak a régi (Pp|Ptk)', j):
            besorolas = 'KORLÁTOZOTT'
        else:
            besorolas = 'irányadó'
        hat.append({'fajl': fajl, 'tetelek': sorted({x[0] for x in hiv[fajl]}), 'jegyzet': j, 'besorolas': besorolas})
    return al, ts, hat, hibak


def nyitott(al):
    return [f for f in al['forrasok'] if f['eloirt'] and f['allapot'] != 'friss']


# ---------- kimenetek ----------
def md(al, hat):
    s = ['# S2 – a korpusz hatályossága: %s' % al['cim'], '',
         '- megkövetelt jogállapot: **%s** (a publikálás várható időpontja utáni állapot); ellenőrizve: %s'
         % (al['jogallapot'], al['ellenorizve']),
         '- módszer: %s' % al['modszer'], '']
    ny = nyitott(al)
    s += ['**S2 ÁLLAPOT: %s**' % ('minden előírt forrás megvan és friss' if not ny else
                                 '%d előírt forrás nyitott (%s)' % (len(ny), ', '.join(f['kod'] for f in ny))), '',
          '## Jogszabályok', '',
          '| Forrás | Előírt | A %s napján hatályos időállapot | A korpusz | Eltérő szakaszok | Érintett tételek |' % al['jogallapot'],
          '|---|---|---|---|---|---|']
    for f in al['forrasok']:
        s.append('| %s – %s | %s | %s | **%s** | %s | %s |' % (
            f['kod'], f['nev'], 'igen (%d tétel)' % len(f['tetelek']) if f['tetelek'] else ('átfogó' if f['eloirt'] else 'nem'),
            f.get('idoallapot') or '–', f['allapot'], ', '.join(f.get('elteres', [])) or '–',
            ', '.join(str(k) for k in f['erintett']) or '–'))
    s += ['', '### Megjegyzések forrásonként', '']
    for f in al['forrasok']:
        if f.get('megjegyzes'):
            s.append('- **%s:** %s' % (f['kod'], f['megjegyzes']))
    s += ['', '## Bírósági iránymutatások (az előírtak)', '',
          'Időállapotuk nincs; a mérce az, hogy a Kúria fenntartotta-e az alkalmazhatóságukat. A fájlok lábjegyzete szerint:', '',
          '| Fájl | Tétel | Besorolás | A Kúria lábjegyzete |', '|---|---|---|---|']
    for h in hat:
        s.append('| %s | %s | %s | %s |' % (h['fajl'][:48], ', '.join(map(str, h['tetelek'])), h['besorolas'], h['jegyzet'][:160] or '–'))
    s += ['', '## Hiánylista és teendők', '']
    for i, t in enumerate(al['teendok'], 1):
        s.append('%d. **%s** – %s' % (i, t['ki'], t['mit']))
    s += ['', '## Következmények a tételmunkára (S5) és az API első olvasására (S1/b)', '']
    s += ['- ' + x for x in al['kovetkezmenyek']]
    return '\n'.join(s) + '\n'


def htmlki(al, hat):
    e = html.escape
    szin = {'friss': '#1b7f3b', 'elavult': '#b3261e', 'hianyzik': '#b3261e'}
    sorok = []
    for f in al['forrasok']:
        link = '<a href="%s" target="_blank" rel="noopener">megnyitás</a>' % e(f['url']) if f.get('url') else '–'
        sorok.append('<tr><td><b>%s</b><br><small>%s</small></td><td>%s</td><td>%s</td>'
                     '<td style="color:%s"><b>%s</b></td><td>%s</td><td>%s</td><td>%s</td></tr>' % (
                         e(f['kod']), e(f['nev']), 'igen' if f['eloirt'] else 'nem', e(f.get('idoallapot') or '–'),
                         szin.get(f['allapot'], '#444'), e(f['allapot']), e(', '.join(f.get('elteres', [])) or '–'),
                         e(', '.join(str(k) for k in f['erintett']) or '–'), link))
    hsor = ''.join('<tr><td>%s</td><td>%s</td><td>%s</td><td><small>%s</small></td></tr>'
                   % (e(h['fajl'][:60]), e(', '.join(map(str, h['tetelek']))), e(h['besorolas']), e(h['jegyzet'][:220])) for h in hat)
    ny = nyitott(al)
    return ('<!doctype html><html lang="hu"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>%s – hatályfigyelő</title><style>body{font:15px/1.45 system-ui,sans-serif;margin:24px;max-width:1200px}'
            'table{border-collapse:collapse;width:100%%;margin:12px 0 28px}td,th{border:1px solid #ccc;padding:6px 8px;'
            'vertical-align:top;text-align:left}th{background:#f3f3f3}small{color:#555}</style>'
            '<h1>%s – hatályfigyelő</h1><p>Megkövetelt jogállapot: <b>%s</b>. Ellenőrizve: %s. Állapot: <b>%s</b>.</p>'
            '<h2>Jogszabályok</h2><table><tr><th>Forrás</th><th>Előírt</th><th>Hatályos időállapot</th><th>A korpusz</th>'
            '<th>Eltérő szakaszok</th><th>Érintett tételek</th><th>Hatályos szöveg</th></tr>%s</table>'
            '<h2>Bírósági iránymutatások</h2><table><tr><th>Fájl</th><th>Tétel</th><th>Besorolás</th><th>A Kúria lábjegyzete</th></tr>%s</table>'
            '</html>\n' % (e(al['cim']), e(al['cim']), e(al['jogallapot']), e(al['ellenorizve']),
                           'minden előírt forrás friss' if not ny else '%d előírt forrás nyitott' % len(ny), ''.join(sorok), hsor))


def manifest_frissit(al):
    ut = os.path.join(K, 'manifest.json')
    m = json.loads(open(ut, encoding='utf-8').read())
    adat = {'korpusz/' + f['fajl']: f for f in al['forrasok']}
    for it in m['items']:
        f = adat.get(it['file'])
        if f:
            it['idoallapot'] = f.get('idoallapot')
            it['hatalyossag'] = {'allapot': f['allapot'], 'jogallapot': al['jogallapot'], 'ellenorizve': al['ellenorizve']}
    open(ut, 'w', encoding='utf-8').write(json.dumps(m, ensure_ascii=False, indent=2) + '\n')


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ('ujjlenyomat', 'jelentes', 'kapu'):
        sys.exit(__doc__)
    if sys.argv[1] == 'ujjlenyomat':
        return ujjlenyomat(sys.argv[2], '--cikk' in sys.argv)
    al, ts, hat, hibak = osszeallit()
    if hibak:
        sys.exit('hatalyossag: HIBA\n' + '\n'.join(hibak))
    ny = nyitott(al)
    if sys.argv[1] == 'jelentes':
        open(os.path.join(GY, 'jelentesek', 'hatalyossag.md'), 'w', encoding='utf-8').write(md(al, hat))
        open(os.path.join(K, 'hatalyok.html'), 'w', encoding='utf-8').write(htmlki(al, hat))
        manifest_frissit(al)
    korl = [h['fajl'] for h in hat if h['besorolas'] == 'KORLÁTOZOTT']
    erintett = sorted({k for f in al['forrasok'] for k in f['erintett']})
    print('hatalyossag: forrás %d, előírt %d, nyitott %d (%s); érintett tétel %d; előírt iránymutatás %d, korlátozott %d'
          % (len(al['forrasok']), sum(1 for f in al['forrasok'] if f['eloirt']), len(ny),
             ', '.join(f['kod'] for f in ny) or '–', len(erintett), len(hat), len(korl)))
    if sys.argv[1] == 'kapu' and ny:
        sys.exit(1)


if __name__ == '__main__':
    main()
