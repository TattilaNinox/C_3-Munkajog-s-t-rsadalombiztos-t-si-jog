#!/usr/bin/env python3
"""Egyezésmérő, 1. fél: a tétel magyarázó bekezdéseinek lenyomatcsomagja a böngészőlapon futó mérőhöz
(tools/kommentar/egyezes.js). Folyamataudit 2026-11-15, B változat (Attila jóváhagyása 20:51).

    python3 tools/egyezes_elokeszit.py NN [--csak-menet 2] [--csak ID[,ID…]] [--darab N] [--ki ÚTVONAL|-]

Cél: gépi előszűrő arra, mennyire áll közel a tétel egy-egy bekezdése a Jogkódex-kommentár szövegéhez – úgy, hogy a
kommentár szövege nem hagyja el a böngészőlapot és nem kerül fájlba. A csomag CSAK lenyomatokat (számokat) és
bekezdés-azonosítókat tartalmaz, tételszöveget sem; a lapról is csak számok és #s azonosítók jönnek vissza.

Eljárás (a JS-oldal betűre ugyanígy számol – a kettő egyezését a próba igazolja):
  1. bekezdések: a kontroll.py leltár „p” blokkjai (tetel_blokk), ugyanazzal az azonosítóval, mint a kontroll/NN.json;
     --csak-menet 2: csak a kontroll-bejegyzésben "menet": 2 jelű bekezdések; --csak: a megadott azonosítók;
  2. normalizálás: NFC, kisbetű; szó = betűk és számjegyek összefüggő sorozata (minden más – írásjel, §, kötőjel – elválaszt);
     a számok megmaradnak; minden szó az első 6 karakterére vágva;
  3. szó-ötösök (5 egymást követő csonkolt szó, egy szóközzel összefűzve) → 32 bites FNV-1a lenyomat az UTF-8 bájtokon;
  4. kivesszük azokat az ötösöket, amelyek a korpusz (korpusz/*.txt, minden fájl) szövegében is előfordulnak – a szó
     szerint idézett normaszöveg nem átvétel;
  5. ritkítás (winnowing, ablak 4): a megmaradt lenyomatsorban minden 4 egymást követő lenyomatból a legkisebb (egyenlőnél
     a jobb szélső) kerül a csomagba, helyenként egyszer; 4-nél rövidebb sorból a legkisebb; ismétlődő lenyomat egyszer.
Kimenet: tömör, egysoros JSON: {"v":1,"b":[["<bekezdés-azonosító>",["<lenyomat base36>",…]],…]};
  --darab N: legfeljebb N karakteres, önállóan érvényes darabok ({"v":1,"d":i,"db":k,"b":[…]}); egy hosszú bekezdés
  lenyomatai két darabra is eshetnek (a JS az azonosító szerint összefűzi).
  Alapértelmezett hely: /tmp/egyezes_NN.json (darabolva /tmp/egyezes_NN_1.json, …); --ki -: a szabványos kimenetre.
  A méretet (karakter) mindig kiírja (--ki - esetén a hibakimenetre).
A korpusz-ötösök halmaza a /tmp/egyezes_korpusz_<lenyomat>.txt gyorsítótárba kerül (a korpusz változásakor újraépül).
A kommentárkötet azonosítója a beállítás kommentar mezője.
"""
import hashlib, json, os, sys, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kozos

SZOHOSSZ = 6
OTOS = 5
ABLAK = 4


def szavak(s):
    s = unicodedata.normalize('NFC', s).lower()
    out, cur = [], []
    for c in s:
        if c.isalnum():
            cur.append(c)
        elif cur:
            out.append(''.join(cur)[:SZOHOSSZ]); cur = []
    if cur:
        out.append(''.join(cur)[:SZOHOSSZ])
    return out


def fnv1a(s):
    h = 0x811c9dc5
    for b in s.encode('utf-8'):
        h ^= b
        h = (h * 0x01000193) & 0xffffffff
    return h


def otosok(s):
    w = szavak(s)
    return [fnv1a(' '.join(w[i:i + OTOS])) for i in range(len(w) - OTOS + 1)]


def winnow(h):
    if not h:
        return []
    if len(h) < ABLAK:
        return [min(h)]
    out, utolso = [], -1
    for i in range(len(h) - ABLAK + 1):
        ab = h[i:i + ABLAK]
        m = min(ab)
        j = i + max(k for k, x in enumerate(ab) if x == m)
        if j != utolso:
            out.append(h[j]); utolso = j
    lat, egyedi = set(), []
    for x in out:
        if x not in lat:
            lat.add(x); egyedi.append(x)
    return egyedi


def b36(x):
    d = '0123456789abcdefghijklmnopqrstuvwxyz'
    if x == 0:
        return '0'
    s = ''
    while x:
        x, r = divmod(x, 36); s = d[r] + s
    return s


def korpusz_otosok():
    fajlok = sorted(f for f in os.listdir(kozos.KORPUSZ) if f.endswith('.txt'))
    ujl = hashlib.sha1()
    for f in fajlok:
        st = os.stat(os.path.join(kozos.KORPUSZ, f))
        ujl.update(f'{f}|{st.st_size}|{int(st.st_mtime)}\n'.encode('utf-8'))
    gy = os.path.join('/tmp', f'egyezes_korpusz_{ujl.hexdigest()[:12]}.txt')
    if os.path.exists(gy):
        return {int(x, 16) for x in open(gy).read().split()}
    hal = set()
    for f in fajlok:
        hal.update(otosok(open(os.path.join(kozos.KORPUSZ, f), encoding='utf-8', errors='replace').read()))
    try:
        with open(gy, 'w') as fh:
            fh.write('\n'.join(format(x, 'x') for x in hal))
    except OSError:
        pass
    return hal


def csomag(n, csak_menet=None, csak=None):
    import kontroll
    d = kontroll.betolt(n)
    menet = {b['id']: b.get('menet') for b in d['bekezdesek']}
    kor = korpusz_otosok()
    out, stat = [], {'bekezdes': 0, 'ures': 0, 'otos': 0, 'korpusz': 0, 'lenyomat': 0}
    for i, _, s in kontroll.bekezdesek(n):
        if csak_menet is not None and menet.get(i) != csak_menet:
            continue
        if csak and i not in csak:
            continue
        h = otosok(s)
        m = [x for x in h if x not in kor]
        w = winnow(m)
        stat['bekezdes'] += 1; stat['otos'] += len(h); stat['korpusz'] += len(h) - len(m); stat['lenyomat'] += len(w)
        stat['ures'] += not w
        out.append([i, [b36(x) for x in w]])
    return out, stat


def darabol(b, n):
    """Legfeljebb n karakteres, önállóan érvényes darabok."""
    def meret(lst, i, k):
        return len(json.dumps({'v': 1, 'd': i, 'db': k, 'b': lst}, separators=(',', ':')))
    darabok, cur = [], []
    for azon, lny in b:
        rest = list(lny)
        while True:
            probe = cur + [[azon, rest]]
            if meret(probe, 99, 99) <= n:
                cur = probe; break
            # ami belefér ebből a bekezdésből
            fer = []
            for x in rest:
                if meret(cur + [[azon, fer + [x]]], 99, 99) > n:
                    break
                fer.append(x)
            if fer:
                cur.append([azon, fer]); rest = rest[len(fer):]
            if not cur:
                raise SystemExit(f'a --darab {n} túl kicsi egyetlen lenyomathoz is')
            darabok.append(cur); cur = []
            if not rest:
                break
    if cur:
        darabok.append(cur)
    k = len(darabok)
    return [json.dumps({'v': 1, 'd': i + 1, 'db': k, 'b': x}, ensure_ascii=False, separators=(',', ':')) for i, x in enumerate(darabok)]


def main(a):
    if not a or a[0] in ('-h', '--help'):
        print(__doc__); return 0
    n = int(a[0]); csak_menet = None; darab = None; ki = None; csak = None
    i = 1
    while i < len(a):
        if a[i] == '--csak-menet':
            csak_menet = int(a[i + 1]); i += 2
        elif a[i] == '--darab':
            darab = int(a[i + 1]); i += 2
        elif a[i] == '--ki':
            ki = a[i + 1]; i += 2
        elif a[i] == '--csak':
            csak = set(a[i + 1].split(',')); i += 2
        else:
            raise SystemExit(f'ismeretlen kapcsoló: {a[i]}')
    b, st = csomag(n, csak_menet, csak)
    teljes = json.dumps({'v': 1, 'b': b}, ensure_ascii=False, separators=(',', ':'))
    darabok = darabol(b, darab) if darab else [teljes]
    info = (f"{n}. tétel: {st['bekezdes']} bekezdés ({st['ures']} lenyomat nélkül – csak korpusz-idézet vagy 5 szónál rövidebb); "
            f"ötös: {st['otos']}, ebből a korpuszban is: {st['korpusz']}; lenyomat a csomagban: {st['lenyomat']}; "
            f"csomag: {len(teljes)} karakter" + (f"; {len(darabok)} darab: " + ', '.join(str(len(x)) for x in darabok) if darab else ''))
    if ki == '-':
        for x in darabok:
            print(x)
        print(info, file=sys.stderr)
        return 0
    if ki is None:
        ki = f'/tmp/egyezes_{n:02d}.json'
    if len(darabok) == 1:
        open(ki, 'w', encoding='utf-8').write(darabok[0]); utak = [ki]
    else:
        alap, kit = os.path.splitext(ki); utak = []
        for j, x in enumerate(darabok, 1):
            p = f'{alap}_{j}{kit}'; open(p, 'w', encoding='utf-8').write(x); utak.append(p)
    print(info)
    print('fájl: ' + ', '.join(utak))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
