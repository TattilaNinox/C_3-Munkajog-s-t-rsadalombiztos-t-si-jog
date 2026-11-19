#!/usr/bin/env python3
"""Az átíró köteg műveletlistáinak alkalmazása az NN.txt-re.

    python3 tools/s5/alkalmaz.py [--ir] [tétel ...]

- Minden műveletet ellenőriz (létező sorok, át nem fedő tartományok, doboz csak egyben törölhető); a hibás művelet
  kimarad, és a jelentésbe kerül.
- Az „@DOBOZ …” elem helyére a doboz a korpuszból épül (fejléc + a kért teljes bekezdések); a modell jogszabályszöveget nem ír.
  §-os és cikkre tagolt forrásra is („@DOBOZ EUMSZ 288. cikk”, „@DOBOZ Alaptörvény XXVIII. cikk (1)”).
- A tiltott szavakat és a gyanús hivatkozásokat (határozatszám, amely a tétel előírt anyagában nincs) jelzi, nem javítja.
- --ir nélkül próbafutás. Kimenet: jelentesek/api/atiras_alkalmazas.md és .json; utolsó sor az összesítő.
"""
import json, os, re, sys

def _gyoker():
    """A tételsor-tároló gyökere: az első szülőmappa, amelyben van tetelsor/beallitas.json."""
    d = os.path.dirname(os.path.abspath(__file__))
    while d != os.path.dirname(d):
        if os.path.isfile(os.path.join(d, 'tetelsor', 'beallitas.json')):
            return d
        d = os.path.dirname(d)
    raise SystemExit('nem találom a tételsor-tároló gyökerét (tetelsor/beallitas.json)')


GY = _gyoker()
sys.path.insert(0, os.path.join(GY, 'tools'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kozos
import alapfelvetel as af
import doboz_javit as dj
import koteg

IR = '--ir' in sys.argv
TETELEK = [int(a) for a in sys.argv[1:] if a.isdigit()]
TILTOTT = re.compile(r'korpusz|tananyag|ZH-felkészítő|kommentár|tankönyv|ebben a tételben|a lelet\b', re.I)
HATAROZAT = re.compile(r'\b(?:BH|EBH|BDT|ÍH|Pfv|Gfv|Mfv|Kfv)\.?\s?[IVX\d][\w./]*\d|\b\d+/\d{4}\.\s*(?:PJE|KPJE|PK|GK|KMK|AB|\([IVX]+\.\s*\d+\.\)\s*AB)', re.U)
JOG = None


def doboz_epit(elem):
    """„@DOBOZ Pp. 427. § (1)-(2)” -> a doboz sorai (fejléc + szöveg) a korpuszból, vagy (None, ok)."""
    fej = elem[len('@DOBOZ'):].strip()
    m = kozos.doboz_fej(fej)
    if not m:
        return None, 'a fejléc nem értelmezhető (vagy az egysége nem a forrásé): ' + fej
    kod, par = kozos.fejlec_kod(m)
    if kod not in JOG or par not in dj.paragrafus_sorok(kod):
        return None, 'nincs ilyen %s a korpuszban: %s' % ('§' if kozos.egyseg(kod) == '§' else 'cikk', fej)
    cs = dj.csoportok(dj.paragrafus_sorok(kod)[par])
    maradek = fej[m.end(3):]
    kert = set()
    for a, b in re.findall(r'\((\d+[a-z]?)\)(?:\s*[–-]\s*\((\d+[a-z]?)\))?', maradek):
        if b:
            kulcsok = [k for k, _ in cs if not k.startswith('hk') and k != 'cim']
            if a in kulcsok and b in kulcsok:
                kert.update(kulcsok[kulcsok.index(a):kulcsok.index(b) + 1])
            else:
                return None, 'nincs ilyen bekezdés: ' + fej
        else:
            kert.add(a)
    if kert:
        hianyzik = [k for k in kert if k not in [x for x, _ in cs]]
        if hianyzik:
            return None, 'nincs ilyen bekezdés: %s (%s)' % (fej, ', '.join(hianyzik))
        sorok = [l for k, ls in cs if k in kert for l in ls]
    else:
        sorok = [l for k, ls in cs if k != 'cim' for l in ls]
    if not sorok:
        return None, 'üres doboz: ' + fej
    return [fej] + sorok, None


def tetel(n):
    p = os.path.join(GY, 'jelentesek', 'api', 'atiras', 'atir-%02d.json' % n)
    if not os.path.exists(p):
        return None
    d = json.load(open(p, encoding='utf-8'))
    ut = os.path.join(GY, '%02d.txt' % n)
    txt = open(ut, encoding='utf-8').read()
    L = txt.split('\n')
    dobozok = [(h, idx) for h, idx in koteg.doboz_sorok(txt) if idx]
    jel = {'tetel': n, 'muvelet': len(d.get('muveletek', [])), 'alkalmazva': 0, 'elvetve': [], 'figyelmeztetes': [],
           'nyitott': len(d.get('nyitott', [])), 'elotte': len(txt)}
    ervenyes, foglalt = [], set()
    eloirt = af.eloirt_szoveg(next(t for t in json.loads(af.be('tetelsor/tetelsor.json'))['tetelek'] if t['sorszam'] == n)) or ''
    for i, mu in enumerate(d.get('muveletek', [])):
        tip = mu.get('tipus')
        try:
            if tip == 'beszuras':
                a = b = int(mu['utan']); tart = range(0)
            else:
                a, b = int(mu['tol']), int(mu.get('ig', mu['tol'])); tart = range(a, b + 1)
        except (KeyError, TypeError, ValueError):
            jel['elvetve'].append({'i': i, 'ok': 'hiányzó vagy hibás sorszám'}); continue
        if tip not in ('csere', 'torles', 'beszuras') or a < 0 or b > len(L) or a > b or (tip != 'beszuras' and a < 1):
            jel['elvetve'].append({'i': i, 'ok': 'érvénytelen művelet vagy tartomány %s–%s' % (a, b)}); continue
        if any(x in foglalt for x in tart):
            jel['elvetve'].append({'i': i, 'ok': 'átfedő tartomány %s–%s' % (a, b)}); continue
        hiba = None
        for h, idx in dobozok:
            teljes = set(range(h + 1, idx[-1] + 2))      # 1-től számozva: fejléc … utolsó dobozsor
            erintett = teljes & set(tart)
            if erintett and not teljes <= set(tart):
                hiba = 'dobozt csak egyben lehet törölni (sor %d–%d)' % (h + 1, idx[-1] + 1); break
            if tip == 'beszuras' and h + 1 <= a < idx[-1] + 1:
                hiba = 'beszúrás doboz belsejébe (sor %d)' % a; break
        if hiba:
            jel['elvetve'].append({'i': i, 'ok': hiba}); continue
        uj = []
        if tip != 'torles':
            elemek = mu.get('uj') or []
            if isinstance(elemek, str):
                elemek = [elemek]
            for e in elemek:
                e = re.sub(r'\s*\n\s*', ' ', str(e)).strip()
                e = re.sub(r'^⟦\d+⟧\s*', '', e)
                if not e:
                    continue
                if e.startswith('@DOBOZ'):
                    sorok, ok = doboz_epit(e)
                    if sorok is None:
                        hiba = ok; break
                    uj.extend(sorok)
                elif e.startswith('[D') or kozos.doboz_fej(e):
                    hiba = 'kézzel írt doboz: ' + e[:60]; break
                else:
                    uj.append(e)
                    if TILTOTT.search(e):
                        jel['figyelmeztetes'].append('tiltott szó: ' + TILTOTT.search(e).group(0) + ' – ' + e[:80])
                    for hm in HATAROZAT.finditer(e):
                        if kozos.norm(hm.group(0)) not in kozos.norm(eloirt) and hm.group(0) not in txt:
                            jel['figyelmeztetes'].append('nem előírt határozat: ' + hm.group(0) + ' – ' + e[:80])
            if hiba:
                jel['elvetve'].append({'i': i, 'ok': hiba}); continue
            if not uj:
                jel['elvetve'].append({'i': i, 'ok': 'üres „uj”'}); continue
        foglalt.update(tart)
        ervenyes.append((a, b, tip, uj))
    for a, b, tip, uj in sorted(ervenyes, key=lambda x: (x[1], x[2] == 'beszuras'), reverse=True):
        blokk = []
        for k, s in enumerate(uj):
            if k:
                blokk.append('')
            blokk.append(s)
        if tip == 'beszuras':
            L[a:a] = ([''] if a and L[a - 1].strip() else []) + blokk + ([''] if a < len(L) and L[a].strip() else [])
        elif tip == 'torles':
            del L[a - 1:b]
        else:
            L[a - 1:b] = blokk
        jel['alkalmazva'] += 1
    uj_txt = re.sub(r'\n{3,}', '\n\n', '\n'.join(L))
    jel['utana'] = len(uj_txt)
    if IR:
        if uj_txt != txt:
            open(ut, 'w', encoding='utf-8').write(uj_txt)
        # az alkalmazott műveletlista az archívumba kerül: kétszer nem alkalmazható (a sorszámok már nem érvényesek)
        arch = os.path.join(GY, 'jelentesek', 'api', 'atiras', 'alkalmazva')
        os.makedirs(arch, exist_ok=True)
        k = 1
        while os.path.exists(os.path.join(arch, 'atir-%02d.k%d.json' % (n, k))):
            k += 1
        os.replace(p, os.path.join(arch, 'atir-%02d.k%d.json' % (n, k)))
    return jel


def main():
    global JOG
    JOG = kozos.korpusz_jogszabalyok()
    ki = []
    for t in kozos.tetelsor()['tetelek']:
        n = t['sorszam']
        if TETELEK and n not in TETELEK:
            continue
        j = tetel(n)
        if j:
            ki.append(j)
    cel = os.path.join(GY, 'jelentesek', 'api')
    json.dump(ki, open(os.path.join(cel, 'atiras_alkalmazas.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    md = ['# Az átíró köteg alkalmazása (%s)' % ('beírva' if IR else 'próbafutás'), '',
          '| Tétel | Művelet | Alkalmazva | Elvetve | Figyelmeztetés | Nyitott pont | Karakter előtte → utána |', '|---|---|---|---|---|---|---|']
    for j in ki:
        md.append('| %d | %d | %d | %d | %d | %d | %d → %d |' % (j['tetel'], j['muvelet'], j['alkalmazva'], len(j['elvetve']),
                                                               len(j['figyelmeztetes']), j['nyitott'], j['elotte'], j['utana']))
    for j in ki:
        if j['elvetve'] or j['figyelmeztetes']:
            md += ['', '## %d. tétel' % j['tetel']] + ['- elvetve (%d. művelet): %s' % (e['i'], e['ok']) for e in j['elvetve']] \
                + ['- ' + f for f in j['figyelmeztetes']]
    open(os.path.join(cel, 'atiras_alkalmazas.md'), 'w', encoding='utf-8').write('\n'.join(md) + '\n')
    print('alkalmaz: tétel %d, művelet %d, alkalmazva %d, elvetve %d, figyelmeztetés %d, nyitott pont %d%s'
          % (len(ki), sum(j['muvelet'] for j in ki), sum(j['alkalmazva'] for j in ki), sum(len(j['elvetve']) for j in ki),
             sum(len(j['figyelmeztetes']) for j in ki), sum(j['nyitott'] for j in ki), '' if IR else ' (próbafutás, --ir nélkül)'))


if __name__ == '__main__':
    main()
