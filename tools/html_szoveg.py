#!/usr/bin/env python3
"""Jogszabály-HTML (Nemzeti Jogszabálytár vagy Jogtár mentett oldala) → a korpusz TXT-formája.

    python3 tools/html_szoveg.py <bemenet.html> <kod> > kimenet.txt
    python3 tools/html_szoveg.py --info <bemenet.html>      # forrás, időállapot, figyelmeztetések (JSON)

A kimenet sorai: „N. §” vagy „N:M. § [cím]” fejléc, „(1) …” bekezdés, „a) …” pont, címsorok.
A lábjegyzetek (Megállapította, Beiktatta, Módosította …) és az oldal kerete kimarad.
Csak olvas; a fájlt nem módosítja. Szükséges: beautifulsoup4, lxml.
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kozos
from bs4 import BeautifulSoup

LABJEGYZET = re.compile(r'^(Megállapította|Beiktatta|Módosította|Módosítva|Hatályon kívül helyezte|Hatálytalan|'
                        r'Lásd:|Szövegcserés módosítás|Számozását módosította|Kiigazította|Az? .{0,40} lép hatályba)')
if kozos.beallitas()['parMinta'] == 'konyv':
    PAR = re.compile(r'^(\d+(?::\d+)?(?:/[A-Z])?)\. §$')
    PAR_SOR = re.compile(r'^(\d+(?::\d+)?(?:/[A-Z])?)\. §\s')
else:
    PAR = re.compile(r'^(\d+(?:/[A-Z])?)\. §$')
    PAR_SOR = re.compile(r'^(\d+(?:/[A-Z])?)\. §\s')
PONT = re.compile(r'^(\(\d+[a-z]?\)|[a-z]{1,2}\)|\d+\.)$')


def sorok(html):
    s = BeautifulSoup(html, 'lxml')
    for t in s(['script', 'style', 'noscript', 'head']):
        t.decompose()
    # lábjegyzet-hivatkozások és -szövegek (Jogszabálytár: .footnote*, Jogtár: a.lbjlink)
    for t in s.select('[class*="footnote"], sup.fnSup, a.lbjlink'):
        t.decompose()
    # Jogszabálytár: a törzsszöveg blokkjai div#sc<év>-…; a teljes mentésben a tartalomjegyzék is benne van,
    # ezért ha vannak ilyen blokkok, csak ezekből dolgozunk (blokkonként egy sor).
    blokk = s.find_all('div', id=re.compile(r'^sc\d{4}-'))
    if blokk:
        L = [re.sub(r'\s+', ' ', b.get_text(' ')).strip() for b in blokk]
        L = [re.sub(r'\[ ', '[', re.sub(r' \]', ']', l)) for l in L if l]
        return [l for l in L if l != '*']
    L = [re.sub(r'\s+', ' ', l).strip() for l in s.get_text('\n').split('\n') if l.strip()]
    return [l for l in L if l != '*']


def info(html):
    L = sorok(html)
    out = {'forras': None, 'idoallapot': None, 'figyelmeztetes': []}
    if 'Nemzeti Jogszabálytár' in html[:20000] or any('Nemzeti Jogszabálytár' == l for l in L[:5]):
        out['forras'] = 'njt'
        teljes = BeautifulSoup(html, 'lxml').get_text(' ')
        m = re.search(r'Hatályos:\s*(\d{4})\.\s*(\d{2})\.\s*(\d{2})\.', teljes)
        if m:
            out['idoallapot'] = {'tol': f'{m.group(1)}-{m.group(2)}-{m.group(3)}', 'ig': None, 'szoveg': m.group(0)}
        for i, l in enumerate(L[:80] if not out['idoallapot'] else []):
            m = re.fullmatch(r'(\d{4})\.(\d{2})\.(\d{2})\.', l)
            if m:
                out['idoallapot'] = {'tol': f'{m.group(1)}-{m.group(2)}-{m.group(3)}', 'ig': None, 'szoveg': l}
                break
    else:
        out['forras'] = 'jogtar'
        for l in L[:60]:
            m = re.match(r'^Hatály: \(?\s*(\d{4})\.([IVX]+)\.(\d+)\.\s*-\s*(?:(\d{4})\.([IVX]+)\.(\d+)\.)?', l)
            if m:
                R = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10, 'XI': 11, 'XII': 12}
                tol = f'{m.group(1)}-{R[m.group(2)]:02d}-{int(m.group(3)):02d}'
                ig = f'{m.group(4)}-{R[m.group(5)]:02d}-{int(m.group(6)):02d}' if m.group(4) else None
                out['idoallapot'] = {'tol': tol, 'ig': ig, 'szoveg': l}
                break
        if any('jogszabály 1. weboldalát tartalmazza' in l for l in L[:60]):
            out['figyelmeztetes'].append('A Jogtár-oldal szerint a mentés a jogszabály 1. weboldala; a teljesség a §-ok számával ellenőrizendő.')
    return out


def szoveg(html, kod):
    L = sorok(html)
    ptk = kozos.konyves(kod)
    rx = re.compile(r'^\d+:\d+(?:/[A-Z])?\. §' if ptk else r'^\d+(?:/[A-Z])?\. §')
    # a törzsszöveg az első §-fejléc előtti utolsó címsortól indul; elég az első §-tól
    start = next((i for i, l in enumerate(L) if rx.match(l)), None)
    if start is None:
        raise SystemExit('Nem található §-fejléc')
    # vissza a fejezet-/alcímekig (legfeljebb 6 sor), hogy a szerkezet megmaradjon
    while start > 0 and not re.match(r'^(Hatály|Jelen dokumentum|Megnyitom|jelek a|\d{4}\.\d{2}\.\d{2}\.|\*$)', L[start - 1]) and start > 0 and len(L[start - 1]) < 120 and not L[start - 1].endswith('.'):
        start -= 1
    out, i = [], start
    while i < len(L):
        l = L[i]
        if LABJEGYZET.match(l):
            # a lábjegyzet-blokk: a dokumentum végén áll; ott a törzsszöveg véget ér
            if all(LABJEGYZET.match(x) or len(x) < 3 for x in L[i:i + 3] if x):
                break
            i += 1; continue
        if l.startswith('Kihirdetve:') or l == 'Lábjegyzetek' or l == '_' or 'sütik' in l or 'cookie' in l.lower():
            break
        if l == '[':  # njt: [ cím ]
            j = L.index(']', i) if ']' in L[i:i + 6] else None
            if j:
                cim = ' '.join(L[i + 1:j]).strip()
                if out and PAR.match(out[-1]):
                    out[-1] += f' [{cim}]'
                else:
                    out.append(f'[{cim}]')
                i = j + 1; continue
        if l.startswith('[') and l.endswith(']') and out and re.match(r'^\d+(?::\d+)?(?:/[A-Z])?\. §$', out[-1]):
            out[-1] += ' ' + l; i += 1; continue  # Jogtár: a § címe külön sorban
        if PONT.match(l) and i + 1 < len(L) and not re.match(r'^\d+(?::\d+)?(?:/[A-Z])?\. §', L[i + 1]) and not PONT.match(L[i + 1].split(' ')[0]):
            out.append(f'{l} {L[i + 1]}'); i += 2; continue
        if l in (')',) and out:
            out[-1] += ')'; i += 1; continue
        out.append(l); i += 1
    # bekezdés-folytatás: a pont után következő, kisbetűvel induló záró rész („kell alkalmazni.”) külön sor marad
    # a dőlt pontjelölés külön elemből jön: „b) ,” → „b),”
    out = [re.sub(r'(\b[a-z]{1,2}\)|\)) ([,.;:])', r'\1\2', l) for l in out]
    return '\n'.join(out).rstrip() + '\n'


if __name__ == '__main__':
    if sys.argv[1] == '--info':
        print(json.dumps(info(open(sys.argv[2], encoding='utf-8').read()), ensure_ascii=False))
    else:
        sys.stdout.write(szoveg(open(sys.argv[1], encoding='utf-8').read(), sys.argv[2]))
