#!/usr/bin/env python3
"""A hangos vázlat hangdokumentumainak (tts_documents) betöltési terve.   python3 tools/vazlat_tts_terv.py

Bemenet: termekek/hangos_vazlat/hang/NN/ (a tools/vazlat_hang.py kimenete) és tts/*/_meta.json (a tétel meglévő
hangdokumentumai; csak a jegyzet audioSource-a számít, a csak csatolt változat nem). Kimenet: termekek/hangos_vazlat/tts_terv.json – tételenként egy új hangdokumentum terve:
  docId (hv_a1_NN), title, hangForras (a tétel meglévő hangdokumentumai sorrendben; ezekről öröklődik a hang),
  fopontok (főpontonként a darabok sorszáma), chunks[{index, fajl, fopont, charCount, sha256, fullText}].
Ellenőrzi: minden tételnek van hangforrása, a darabok 1-től folytonosak, egyik darab sem hosszabb 5000 karakternél,
minden darab „[serious]” címkével kezdődik, és a darabok szövege bájtra egyezik a hang/NN/ fájlokkal.
hangHash (2026-11-18, a korábbi hangCommit helyett, amely a commit előtti HEAD-et rögzítette): a hang/NN/*.txt darabfájlok
tartalom-lenyomata – sha256 a fájlok tároló-gyökérhez viszonyított útvonala szerint rendezve, fájlonként
„útvonal NUL tartalom NUL” alakban; ugyanarra a darabszövegre a commit-állapottól függetlenül ugyanaz.
"""
import glob, hashlib, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kozos

HANG = os.path.join(kozos.GYOKER, 'termekek', 'hangos_vazlat', 'hang')
KI = os.path.join(kozos.GYOKER, 'termekek', 'hangos_vazlat', 'tts_terv.json')
MAX = 5000
KIHAGYOTT = []


def tetel_forrasai():
    m = {}
    for f in glob.glob(os.path.join(kozos.GYOKER, 'tts', '*', '_meta.json')):
        d = json.load(open(f, encoding='utf-8'))
        if d.get('via') != 'audioSource':
            # Csak az a hangdokumentum hangforrás, amelyet a jegyzet ténylegesen lejátszik (a jegyzet audioSource-a).
            # A jegyzethez csak csatolt (attachedToNoteId) másik változat kimarad: annak hangja eltérhet (5. tétel).
            KIHAGYOTT.append({'ttsId': d['ttsId'], 'via': d.get('via'), 'title': d['title']})
            continue
        n = None
        jt = kozos.jegyzet_tetel()     # új szerkezet: a tétel a noteId-ből (a tagPath tételcsoportot is tartalmaz)
        if jt is not None:
            n = jt.get(d.get('noteId'))
        else:
            for x in d['tagPath'].split(' > ')[1:] + [d['title']]:
                g = re.match(r'\s*(\d+)\.\s', x)
                if g:
                    n = int(g.group(1)); break
        if n is None:
            raise SystemExit(f'Nem állapítható meg a tétel: {d["ttsId"]} | {d["tagPath"]} | {d["title"][:60]}')
        m.setdefault(n, []).append(d)
    return m


def sorrend(d):
    g = re.match(r'\s*\(([IVX]+)', d['title'])
    rom = {'I': 1, 'V': 5, 'X': 10}
    if not g:
        return (0, d['title'])
    s = g.group(1); v = 0
    for i, c in enumerate(s):
        v += -rom[c] if i + 1 < len(s) and rom[c] < rom[s[i + 1]] else rom[c]
    return (v, d['title'])


def main():
    ts = kozos.tetelsor()
    forr = tetel_forrasai()
    hiba = []; dok = []
    for t in ts['tetelek']:
        n = t['sorszam']; k = f'{n:02d}'
        meta = json.load(open(os.path.join(HANG, k, '_meta.json'), encoding='utf-8'))
        if n not in forr:
            hiba.append(f'{n}. tétel: nincs meglévő hangdokumentum'); continue
        hf = sorted(forr[n], key=sorrend)
        chunks = []; fop = []
        for f in meta['fopontok']:
            idx = []
            for x in f['darabok']:
                szov = open(os.path.join(HANG, k, x['fajl']), encoding='utf-8').read()
                i = len(chunks) + 1
                if len(szov) > MAX:
                    hiba.append(f'{n}. tétel {x["fajl"]}: {len(szov)} karakter')
                if not szov.startswith('[serious]'):
                    hiba.append(f'{n}. tétel {x["fajl"]}: nem [serious] címkével kezdődik')
                if len(szov) != x['karakter']:
                    hiba.append(f'{n}. tétel {x["fajl"]}: a hossz nem egyezik a _meta.json-nal')
                chunks.append({'index': i, 'fajl': x['fajl'], 'fopont': f['fopont'], 'charCount': len(szov),
                               'sha256': hashlib.sha256(szov.encode('utf-8')).hexdigest(), 'fullText': szov})
                idx.append(i)
            fop.append({'fopont': f['fopont'], 'cim': f['cim'], 'chunkok': idx})
        dok.append({'docId': f"hv_{kozos.beallitas()['azon']}_{k}", 'sorszam': n, 'cim': t['cim'], 'title': f'Hangos vázlat – {n}. {t["cim"]}',
                    'hangForras': [d['ttsId'] for d in hf], 'hangForrasCim': [d['title'] for d in hf],
                    'jegyzet': sorted({d['noteId'] for d in hf}), 'fopontok': fop, 'chunks': chunks})
    if hiba:
        raise SystemExit('\n'.join(hiba))
    lenyomat = hashlib.sha256()
    for f in sorted(glob.glob(os.path.join(HANG, '*', '*.txt'))):
        lenyomat.update(os.path.relpath(f, kozos.GYOKER).replace(os.sep, '/').encode('utf-8') + b'\0')
        lenyomat.update(open(f, 'rb').read() + b'\0')
    ex = os.path.join(kozos.GYOKER, 'EXPORT.json')   # új tételsoron (nincs élő export a tárolóban) a tetelsorId: null
    terv = {'sema': 1, 'termek': 'hangos_vazlat_tts', 'tetelsorId': json.load(open(ex, encoding='utf-8'))['tetelsorId'] if os.path.exists(ex) else None,
            'hangHash': lenyomat.hexdigest(),
            'kihagyottHangdokumentum': KIHAGYOTT,
            'osszesites': {'dokumentum': len(dok), 'darab': sum(len(d['chunks']) for d in dok),
                           'karakter': sum(c['charCount'] for d in dok for c in d['chunks']),
                           'hangForras': sum(len(d['hangForras']) for d in dok),
                           'legnagyobbDarab': max(c['charCount'] for d in dok for c in d['chunks'])},
            'dokumentumok': dok}
    json.dump(terv, open(KI, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps(terv['osszesites'], ensure_ascii=False), terv['hangHash'][:12])


if __name__ == '__main__':
    main()
