#!/usr/bin/env python3
"""Várható ElevenLabs-költség a tételsor élesítéséhez (kötelező a tételsor végén, Attila döntése, 2026-11-13).

    python3 tools/hang_koltseg.py --alap=<ref> [--alap=<ref> …]
    # A/1: --alap=origin/elo-2026-11-10-1642 --alap=origin/hangpotlas-2026-11-12 --alap=origin/hangpotlas-2-2026-11-12
    # (az élő export + minden azóta élesbe töltött hangág; a darab akkor változatlan, ha a szövege bármelyikben
    #  ugyanabban a hangdokumentumban megvan – így az elcsúszott sorszámú, de változatlan darab nem számít újnak)

Mit számol (karakter = amit az ElevenLabs számláz: a darab teljes szövege, audiotagekkel, szóközzel):
  A) a tétel meglévő hangdokumentumai: a tts/*/ darabjai közül, amelyek az alaphoz képest újak vagy módosultak
     (az IM-2 után ezeket kell újragenerálni; a változatlan darab hangja megmarad);
  B) a hangos vázlat új hangdokumentumai: termekek/hangos_vazlat/tts_terv.json minden darabja;
  C) tartalék az újrageneráláshoz (hibás kiejtés, meghallgatás utáni javítás): tools/hang_ar.json tartalek_szazalek.
Az árak a tools/hang_ar.json-ból jönnek (forrás és lekérés dátuma ott); a kalkuláció ezt a dátumot kiírja.
Kimenet: jelentesek/hang_koltseg.md és .json. Csak olvas, a tárolóban mást nem ír.
"""
import glob, json, math, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kozos

G = kozos.GYOKER


def git(*a):
    r = subprocess.run(['git', *a], cwd=G, capture_output=True)
    return r.stdout.decode('utf-8') if r.returncode == 0 else None


def elo_szovegek(refs, tid):
    """A hangdokumentum darabjainak szövegei az alapokban (NFC), és hogy létezett-e a dokumentum."""
    out, volt = set(), False
    for ref in refs:
        lista = git('ls-tree', '--name-only', f'{ref}:tts/{tid}/') or ''
        for nev in lista.split('\n'):
            if nev.startswith('chunk_') and nev.endswith('.txt'):
                volt = True
                t = git('show', f'{ref}:tts/{tid}/{nev}')
                if t is not None:
                    out.add(kozos.nfc(t))
    return out, volt


def ezres(x, tized=False):
    return (f'{x:,.2f}' if tized else f'{x:,.0f}').replace(',', ' ')


def main():
    kozos.beallitas()['hangAlapAgak']  # kulcs-ellenőrzés; az --alap kötelező marad, nincs csendes alapérték
    refs = [a.split('=', 1)[1] for a in sys.argv[1:] if a.startswith('--alap=')]
    if not refs:
        raise SystemExit('Kötelező: --alap=<git-hivatkozás> (az élő export és minden azóta élesbe töltött hangág)')
    for ref in refs:
        if git('rev-parse', '--verify', '-q', ref) is None:
            raise SystemExit(f'Az alap ({ref}) nem található: git fetch origin <ág>')
    ref = ' + '.join(refs)
    ar = json.load(open(os.path.join(G, 'tools', 'hang_ar.json'), encoding='utf-8'))

    # A) a tétel hangdokumentumainak változott darabjai
    terv = os.path.join(G, 'termekek', 'hangos_vazlat', 'tts_terv.json')
    tterv = json.load(open(terv, encoding='utf-8')) if os.path.exists(terv) else {'dokumentumok': []}
    hova = {}
    for d in tterv['dokumentumok']:
        for t in d.get('hangForras', []):
            hova[t] = str(d['sorszam'])
    A = {'uj': [0, 0], 'modositott': [0, 0]}; dok = set(); tetelenkent = {}
    for mappa in sorted(glob.glob(os.path.join(G, 'tts', '*', ''))):
        tid = os.path.basename(os.path.dirname(mappa))
        elo, volt = elo_szovegek(refs, tid)
        meta = os.path.join(mappa, '_meta.json')
        tp = json.load(open(meta, encoding='utf-8')).get('tagPath', '') if os.path.exists(meta) else ''
        tetel = hova.get(tid) or (tp.split('>')[-1].strip().split('.')[0] if '>' in tp else '?')
        for f in sorted(glob.glob(os.path.join(mappa, 'chunk_*.txt'))):
            szoveg = kozos.nfc(open(f, encoding='utf-8').read())
            if szoveg in elo:
                continue
            k = 'modositott' if volt else 'uj'
            A[k][0] += 1; A[k][1] += len(szoveg); dok.add(tid)
            tetelenkent[tetel] = tetelenkent.get(tetel, 0) + len(szoveg)
    a_kar = A['uj'][1] + A['modositott'][1]

    # B) a hangos vázlat új hangdokumentumai
    b_db = b_kar = b_dok = 0
    for d in tterv['dokumentumok']:
        b_dok += 1
        for c in d['chunks']:
            b_db += 1; b_kar += len(c['fullText'])

    ossz = a_kar + b_kar
    tart = math.ceil(ossz * ar['tartalek_szazalek'] / 100)
    mind = ossz + tart
    usd = lambda k: k / 1000 * ar['ar_1000_karakter_usd']

    sor = []
    sor.append('# Várható ElevenLabs-költség – a tételsor élesítése')
    sor.append('')
    sor.append(f"**Összesen: {ezres(mind)} karakter ≈ {ezres(usd(mind))} USD** ({ar['modell']}, {ar['ar_1000_karakter_usd']} USD / 1000 karakter; "
               f"ár lekérve: {ar['lekerve']}, {ar['forras']}). Ebből tartalék {ar['tartalek_szazalek']}%: {ezres(tart)} karakter.")
    sor.append('')
    sor.append(f'Alap (élő állapot): `{ref}`. Generálta: `tools/hang_koltseg.py`. A szám becslés: a tényleges költség a meghallgatás utáni újragenerálásoktól függ.')
    sor.append('')
    sor.append('| Tétel | Darab | Karakter | ≈ USD |')
    sor.append('|---|---|---|---|')
    sor.append(f"| A) a tétel hangja – új vagy módosult darab, meglévő hangdokumentumban | {A['modositott'][0]} | {ezres(A['modositott'][1])} | {ezres(usd(A['modositott'][1]), True)} |")
    sor.append(f"| A) a tétel hangja – darab új hangdokumentumban | {A['uj'][0]} | {ezres(A['uj'][1])} | {ezres(usd(A['uj'][1]), True)} |")
    sor.append(f"| B) hangos vázlat – {b_dok} új hangdokumentum | {b_db} | {ezres(b_kar)} | {ezres(usd(b_kar), True)} |")
    sor.append(f"| C) tartalék ({ar['tartalek_szazalek']}%) | – | {ezres(tart)} | {ezres(usd(tart), True)} |")
    sor.append(f"| **Összesen** | | **{ezres(mind)}** | **{ezres(usd(mind), True)}** |")
    sor.append('')
    sor.append(f'Érintett meglévő hangdokumentum: {len(dok)}.')
    sor.append('')
    sor.append('## Előfizetési tervek (a havi keret karakterben)')
    sor.append('')
    sor.append('| Terv | Havidíj | Havi keret | Hány hónap keret kell | Ha egy hónapban, túllépéssel |')
    sor.append('|---|---|---|---|---|')
    for t in ar['tervek']:
        ho = math.ceil(mind / t['karakter'])
        tul = max(0, mind - t['karakter'])
        sor.append(f"| {t['nev']} | {t['havi_usd']} USD | {ezres(t['karakter'])} | {ho} | {ezres(t['havi_usd'] + usd(tul))} USD |")
    sor.append('')
    sor.append('## A tétel hangja tételenként (karakter, A rész)')
    sor.append('')
    sor.append(', '.join(f'{k}.: {ezres(v)}' for k, v in sorted(tetelenkent.items(), key=lambda x: (len(x[0]), x[0]))) or 'nincs változás')
    sor.append('')
    os.makedirs(os.path.join(G, 'jelentesek'), exist_ok=True)
    with open(os.path.join(G, 'jelentesek', 'hang_koltseg.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(sor))
    with open(os.path.join(G, 'jelentesek', 'hang_koltseg.json'), 'w', encoding='utf-8') as f:
        json.dump({'alap': ref, 'ar': ar, 'A': A, 'B': {'dokumentum': b_dok, 'darab': b_db, 'karakter': b_kar},
                   'tartalek': tart, 'osszes_karakter': mind, 'usd': round(usd(mind), 2)}, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print('\n'.join(sor[:3]))


if __name__ == '__main__':
    main()
