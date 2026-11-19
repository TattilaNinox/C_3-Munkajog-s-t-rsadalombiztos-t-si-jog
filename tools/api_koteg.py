#!/usr/bin/env python3
"""A Claude API kötegelt (Message Batches) futtatása a tételsor első olvasásához – a keret gépi védelmével.

    python3 tools/api_koteg.py keszit elso_olvasas [--tetel=1,2,3]   # kérések + költségterv (nem küld, kulcs nem kell)
    python3 tools/api_koteg.py kuld elso_olvasas --plafon=25         # beküldés (ANTHROPIC_API_KEY a környezetben)
    python3 tools/api_koteg.py allapot elso_olvasas                  # hol tart a köteg
    python3 tools/api_koteg.py letolt elso_olvasas                   # eredmények + tényleges költség a főkönyvbe
    python3 tools/api_koteg.py fokonyv                               # eddigi költés és a maradék keret

Szabályok (12_tetelsor_szabvany.md, 13_api_keret.md):
- A kulcs csak környezeti változóból jön; fájlba, naplóba, kimenetre nem kerül.
- A kérésbe csak a tároló saját tartalma megy: a publikált jegyzet, a kiírás és a korpusz (közzétett jog).
  Kommentár, IJOTEN, felhasználói adat nem.
- Küldés csak akkor, ha a legrosszabb eset költsége a --plafon alatt van, és a főkönyv szerinti eddigi költéssel
  együtt belefér a tételsor keretébe (tetelsor/beallitas.json: apiKeretUsd).
- Az eredmény lelet: a tételmunka bemenete. Szöveget nem ír át, tételt nem zár le; a kapukat nem váltja ki.

Csak a standard könyvtárat használja; Python 3.9-től fut. Az árak forrása: platform.claude.com/docs (2026-11-19).
"""
import csv, datetime, html.parser, json, os, re, sys, urllib.error, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import alapfelvetel as af

GY = af.GY
API = 'https://api.anthropic.com/v1/messages/batches'
VERZIO = '2026-10-21'
# kötegelt ár, USD / millió token (a normál ár fele); ellenőrizve: 2026-11-19
ARAK = {'claude-opus-5-5': {'be': 2.0, 'ki': 10.0, 'cache_iras': 4.0, 'cache_olvas': 0.10}}
KAR_PER_TOKEN = 2.2        # óvatos becslés magyar szövegre; a tényleges tokenszámot az eredmény usage mezője adja
FOKONYV = os.path.join(GY, 'jelentesek', 'api_koltseg.csv')
FEJ = ['datum', 'feladat', 'koteg', 'modell', 'keres', 'sikeres', 'be_token', 'ki_token', 'cache_iras_token', 'cache_olvas_token', 'usd']


def arg(nev, alap=None):
    for a in sys.argv:
        if a.startswith('--%s=' % nev):
            return a.split('=', 1)[1]
    return alap


def mappa(feladat):
    m = os.path.join(GY, 'ki', 'api', feladat)
    os.makedirs(m, exist_ok=True)
    return m


# ---------- a jegyzet HTML-je olvasható szöveggé ----------
class Szoveg(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ki, self.verem, self.spanok = [], [], []

    def handle_starttag(self, tag, attrs):
        osztaly = dict(attrs).get('class') or ''
        if tag == 'span':
            # blokkszintű span (a felsorolás pontja a dobozban): sortörés előtte és utána
            stilus = re.sub(r'\s+', '', dict(attrs).get('style') or '')
            blokk = 'jogszabaly-pont' in osztaly or 'display:block' in stilus
            self.spanok.append(blokk)
            if blokk:
                self.ki.append('\n')
            return
        doboz = tag == 'div' and 'jogszabaly-doboz' in osztaly
        self.verem.append((tag, doboz))
        if tag in ('h1', 'h2', 'h3', 'h4'):
            self.ki.append('\n\n' + '#' * int(tag[1]) + ' ')
        elif doboz:
            self.ki.append('\n\n[DOBOZ] ')
        elif tag in ('p', 'li', 'tr', 'div'):
            self.ki.append('\n\n' if tag != 'li' else '\n- ')
        elif tag == 'br':
            self.ki.append('\n')

    def handle_endtag(self, tag):
        if tag == 'span':
            if self.spanok and self.spanok.pop():
                self.ki.append('\n')
            return
        while self.verem:
            t, doboz = self.verem.pop()
            if doboz:
                self.ki.append(' [/DOBOZ]')
            if t == tag:
                break

    def handle_data(self, d):
        self.ki.append(d)


def jegyzet_szoveg(fajl):
    p = Szoveg()
    p.feed(af.be(fajl))
    s = ''.join(p.ki)
    return '\n'.join(sor.strip() for sor in s.split('\n')).replace('\n\n\n', '\n\n').strip()


# ---------- a feladat: első olvasás ----------
RENDSZER = """Jogi szakvizsga-felkészítő tétel első olvasását végzed (magyar polgári eljárásjog és kapcsolódó jogterületek). \
Négy szöveget kapsz: (1) a hivatalos kiírás tételét, (2) a tételhez előírt joganyag HATÁLYOS szövegét a korpuszból, \
(2/b) azoknak a szakaszoknak a hatályos szövegét, amelyeket a jegyzet dobozban idéz, de a kiírás nem ír elő, \
(3) a publikált jegyzet szövegét (a [DOBOZ] … [/DOBOZ] közötti rész szó szerinti jogszabály-idézet akar lenni).

A feladatod LELET készítése, nem a jegyzet átírása. Szabályok:
- Mérce kizárólag a kapott joganyag: a (2) és a (2/b) rész. Saját tudásból nem javítasz: ha egy állítást a kapott \
joganyag nem dönt el, az NEM_IGAZOLHATO (nem hiba), és megnevezed, milyen forrás döntené el.
- KIIRASON_KIVUL: az állítás olyan szabályról szól, amely a kiírás előírásán kívül esik, ÉS a szövegét nem kaptad meg \
(sem a (2), sem a (2/b) részben). Ezt ne NEM_IGAZOLHATO-nak jelöld: a tételmunka külön kezeli. Egy sorban add meg, \
melyik jogszabályhely döntené el.
- ELLENTMOND: a jegyzet állítása ellentétes a kapott szöveggel (rossz határidő, feltétel, kivétel, alany, joghatás, §-szám).
- PONTATLAN: a lényeg jó, de a megfogalmazás szűkebb, tágabb vagy félreérthető a kapott szöveghez képest.
- ELAVULT_GYANU: a jegyzet olyan szabályt, §-számot vagy szöveget idéz, amely a kapott hatályos szövegben másként áll vagy nincs meg.
- Dobozok: minden [DOBOZ] szövegét vesd össze betűre a kapott joganyaggal; csak az eltérőt, csonkát vagy a kapott \
anyagban nem találhatót jelezd.
- A lefedettség csak a (2) részre vonatkozik; a (2/b) rész a dobozok és az állítások ellenőrzéséhez kell.
- Lefedettség: a kiírás minden előírt egységéről (§, cikk, határozat) mondd meg, hogy a jegyzet tárgyalja, részben tárgyalja vagy hiányzik.
- Idézetet a jegyzetből legfeljebb 200 karakterrel adj, a helyét a legközelebbi címsorral jelöld.
- Ne találgass: amit nem tudsz a kapott szövegből megítélni, azt hagyd ki vagy jelöld NEM_IGAZOLHATO-nak.

A válasz KIZÁRÓLAG egyetlen JSON-objektum, magyarázó szöveg nélkül, ezzel a szerkezettel:
{"tetel": <szám>,
 "lefedettseg": [{"eloiras": "Pp. 8. §", "allapot": "targyalja|reszben|hianyzik", "megjegyzes": ""}],
 "allitasok": [{"hely": "címsor", "tipus": "ELLENTMOND|PONTATLAN|NEM_IGAZOLHATO|KIIRASON_KIVUL|ELAVULT_GYANU", "idezet": "", "korpusz": "Pp. 12. § (1) bekezdés", "indok": ""}],
 "dobozok": [{"hely": "címsor", "hivatkozas": "Pp. 8. §", "gond": "elter|csonka|nincs_a_kapott_anyagban", "reszlet": ""}],
 "elhatarolasok": ["A és B – a szempont megnevezésével"],
 "termekotletek": {"dontesi_fa": [""], "szamolo": [""], "fogalommatrix": [""]},
 "osszegzes": "3–5 mondat: a jegyzet állapota a kapott joganyaghoz képest"}"""


def TARGY():
    """A tárgy megnevezése a rendszerüzenetben a beállításból (A/2-n a korábbi szöveg marad)."""
    B = af.beallitas()
    return 'magyar polgári eljárásjog és kapcsolódó jogterületek' if B.get('azon') == 'a2' else 'magyar jog – %s' % B.get('kategoria', B['cim'])


EXTRA_MAX_DB, EXTRA_MAX_KAR, HOSSZU_JEGYZET, HOSSZU_MAX_KI = 40, 60000, 80000, 32000


def idezett_szakaszok(t, jegyzet_szovegek):
    """A jegyzet dobozaiban idézett, a kiírás által nem előírt szakaszok hatályos szövege a korpuszból.
    Vissza: (szöveg, felvett darab, kihagyott darab). A doboz fejléce az első nem üres sor a [DOBOZ] után."""
    B = af.beallitas()
    fajlok = af.korpusz_fajlok()
    eloirt, egesz = set(), set()
    for h in t['hivatkozasok']:
        if h['tol'] is None:
            egesz.add(h['fajl'])
            continue
        _, idx, rend = af.index(h['fajl'], h['egyseg'])
        for e in rend[rend.index(h['tol']):rend.index(h['ig']) + 1]:
            eloirt.add((h['fajl'], e))
    talalt = []
    for szov in jegyzet_szovegek:
        for m in re.finditer(r'\[DOBOZ\]\s*([^\n]+)', szov):
            fej = m.group(1).strip()
            for f in B['forrasok']:
                illik = None
                for minta in f['mintak']:
                    illik = re.match(minta, fej)
                    if illik:
                        break
                if not illik:
                    continue
                fajl = f.get('fajl') or af.fajl_keres(f['fajlKezdet'], fajlok)
                egys = af.egysegek(fej[illik.end():], f['egyseg'])
                if not fajl or af.nfc(fajl) not in fajlok or not egys:
                    break
                tol = egys[0][0]
                if fajl in egesz or (fajl, tol) in eloirt or (f, fajl, tol) in talalt:
                    break
                if tol in af.index(fajl, f['egyseg'])[1]:
                    talalt.append((f, fajl, tol))
                break
    reszek, kar, kihagyott = [], 0, 0
    for f, fajl, tol in talalt:
        szov = af.tartomany_szoveg(fajl, f['egyseg'], tol, tol)
        if len(reszek) >= EXTRA_MAX_DB or kar + len(szov) > EXTRA_MAX_KAR:
            kihagyott += 1
            continue
        reszek.append(af.egyseg_fej(f['kod'], tol, tol, f['egyseg'], f.get('nev', '')) + '\n' + szov)
        kar += len(szov)
    return '\n\n'.join(reszek), len(reszek), kihagyott


def max_ki_tetelre(t, max_ki):
    """A hosszú jegyzetű tétel nagyobb kimeneti plafont kap (a próba szerint a 24 000 ott szűk)."""
    return max(max_ki, HOSSZU_MAX_KI) if sum(j['karakter'] for j in t['jegyzetek']) >= HOSSZU_JEGYZET else max_ki


def keres_elso_olvasas(t, modell, max_ki):
    szovegek = [jegyzet_szoveg(j['fajl']) for j in t['jegyzetek']]
    extra, extra_db, extra_ki = idezett_szakaszok(t, szovegek)
    max_ki = max_ki_tetelre(t, max_ki)
    jegyz = '\n\n'.join('===== JEGYZETRÉSZ %d/%d: %s =====\n%s' % (i + 1, len(t['jegyzetek']), j['cim'], szovegek[i])
                        for i, j in enumerate(t['jegyzetek']))
    eloirt = af.eloirt_szoveg(t) or '(a kiírás ehhez a tételhez a korpuszban meglévő forrást nem jelöl meg)'
    extra_resz = extra or '(a jegyzet dobozai a kiíráson kívüli szakaszt nem idéznek, vagy az a korpuszban nem található)'
    if extra_ki:
        extra_resz += '\n\n(Terjedelmi okból további %d idézett szakasz szövege nem szerepel itt.)' % extra_ki
    tartalom = ('# (1) A KIÍRÁS TÉTELE\n%d. %s\n\n# (2) AZ ELŐÍRT JOGANYAG HATÁLYOS SZÖVEGE (korpusz)\n%s\n\n'
                '# (2/b) A JEGYZETBEN IDÉZETT, A KIÍRÁSON KÍVÜLI SZAKASZOK HATÁLYOS SZÖVEGE (korpusz)\n%s\n\n# (3) A PUBLIKÁLT JEGYZET\n%s'
                % (t['sorszam'], t['szoveg'], eloirt, extra_resz, jegyz))
    return {'custom_id': 'elso-%02d' % t['sorszam'],
            'params': {'model': modell, 'max_tokens': max_ki, 'system': RENDSZER.replace('magyar polgári eljárásjog és kapcsolódó jogterületek', TARGY()),
                       'messages': [{'role': 'user', 'content': tartalom}]}}


FELADATOK = {'elso_olvasas': keres_elso_olvasas}


# ---------- főkönyv, keret ----------
def fokonyv_sorok():
    if not os.path.exists(FOKONYV):
        return []
    return list(csv.DictReader(open(FOKONYV, encoding='utf-8')))


def koltott():
    return sum(float(s['usd']) for s in fokonyv_sorok())


def keret():
    return float(af.beallitas().get('apiKeretUsd', 0))


def usd(modell, be=0, ki=0, ciras=0, colvas=0):
    a = ARAK[modell]
    return (be * a['be'] + ki * a['ki'] + ciras * a['cache_iras'] + colvas * a['cache_olvas']) / 1e6


# ---------- parancsok ----------
def keszit(feladat):
    modell = arg('modell', 'claude-opus-5-5')
    max_ki = int(arg('max-ki', '24000'))
    if modell not in ARAK:
        sys.exit('Ismeretlen modell (nincs ára a programban): %s' % modell)
    ts = json.loads(af.be('tetelsor/tetelsor.json'))
    szuk = {int(x) for x in (arg('tetel', '') or '').split(',') if x.strip()}
    m = mappa(feladat)
    sorok, be_kar, ki_max = [], 0, 0
    for t in ts['tetelek']:
        if szuk and t['sorszam'] not in szuk:
            continue
        k = FELADATOK[feladat](t, modell, max_ki)
        sorok.append(json.dumps(k, ensure_ascii=False))
        be_kar += len(k['params']['system']) + len(k['params']['messages'][0]['content'])
        ki_max += k['params']['max_tokens']
    open(os.path.join(m, 'keres.jsonl'), 'w', encoding='utf-8').write('\n'.join(sorok) + '\n')
    be_tok = int(be_kar / KAR_PER_TOKEN)
    terv = {'feladat': feladat, 'modell': modell, 'keres': len(sorok), 'be_karakter': be_kar, 'be_token_becsles': be_tok,
            'max_ki_token': max_ki, 'max_ki_token_osszesen': ki_max,
            'varhato_usd': round(usd(modell, be=be_tok, ki=ki_max * 0.4), 2),
            'legrosszabb_usd': round(usd(modell, be=int(be_tok * 1.3), ki=ki_max), 2),
            'megjegyzes': 'A várható érték a kimeneti plafon 40%-ával számol; a legrosszabb eset a teljes plafonnal és 30%-kal több bemenettel.'}
    json.dump(terv, open(os.path.join(m, 'terv.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('keszit: %s – %d kérés, bemenet kb. %d token; várható %.2f USD, legrosszabb eset %.2f USD; keret %.2f, eddig költve %.2f'
          % (feladat, len(sorok), be_tok, terv['varhato_usd'], terv['legrosszabb_usd'], keret(), koltott()))


def hivas(ut, adat=None):
    kulcs = os.environ.get('ANTHROPIC_API_KEY')
    if not kulcs:
        sys.exit('Nincs ANTHROPIC_API_KEY a környezetben. (A kulcsot fájlba ne írd.)')
    k = urllib.request.Request(ut, data=json.dumps(adat).encode('utf-8') if adat is not None else None,
                               headers={'x-api-key': kulcs, 'anthropic-version': VERZIO, 'content-type': 'application/json'})
    try:
        with urllib.request.urlopen(k, timeout=600) as v:
            return v.read()
    except urllib.error.HTTPError as e:
        sys.exit('API-hiba %s: %s' % (e.code, e.read().decode('utf-8', 'replace')[:600]))


def kuld(feladat):
    m = mappa(feladat)
    terv = json.load(open(os.path.join(m, 'terv.json'), encoding='utf-8'))
    plafon = arg('plafon')
    if plafon is None:
        sys.exit('Kötelező: --plafon=<USD> (e fölött a köteg nem megy el).')
    if terv['legrosszabb_usd'] > float(plafon):
        sys.exit('A legrosszabb eset (%.2f USD) a plafon (%s USD) fölött van. Nem küldtem.' % (terv['legrosszabb_usd'], plafon))
    if koltott() + terv['legrosszabb_usd'] > keret():
        sys.exit('A keret nem elég: eddig %.2f + legrosszabb eset %.2f > keret %.2f USD. Nem küldtem.' % (koltott(), terv['legrosszabb_usd'], keret()))
    if os.path.exists(os.path.join(m, 'koteg.json')) and '--ujra' not in sys.argv:
        sys.exit('Ehhez a feladathoz már van beküldött köteg (ki/api/%s/koteg.json). Új küldés csak --ujra kapcsolóval.' % feladat)
    kerelmek = [json.loads(s) for s in open(os.path.join(m, 'keres.jsonl'), encoding='utf-8') if s.strip()]
    v = json.loads(hivas(API, {'requests': kerelmek}))
    json.dump({'id': v['id'], 'bekuldve': v.get('created_at'), 'modell': terv['modell'], 'keres': len(kerelmek)},
              open(os.path.join(m, 'koteg.json'), 'w', encoding='utf-8'), indent=1)
    print('kuld: köteg %s, %d kérés; állapot: %s' % (v['id'], len(kerelmek), v.get('processing_status')))


def allapot(feladat):
    k = json.load(open(os.path.join(mappa(feladat), 'koteg.json'), encoding='utf-8'))
    v = json.loads(hivas('%s/%s' % (API, k['id'])))
    print('allapot: %s – %s; %s' % (k['id'], v.get('processing_status'), json.dumps(v.get('request_counts'))))
    return v


def json_ki(szoveg):
    a, b = szoveg.find('{'), szoveg.rfind('}')
    if a < 0 or b <= a:
        return None
    try:
        return json.loads(szoveg[a:b + 1])
    except ValueError:
        return None


def letolt(feladat):
    m = mappa(feladat)
    k = json.load(open(os.path.join(m, 'koteg.json'), encoding='utf-8'))
    if allapot(feladat).get('processing_status') != 'ended':
        sys.exit('A köteg még nem zárult le; később futtasd újra.')
    nyers = hivas('%s/%s/results' % (API, k['id'])).decode('utf-8')
    open(os.path.join(m, 'eredmeny.jsonl'), 'w', encoding='utf-8').write(nyers)
    cel = os.path.join(GY, 'jelentesek', 'api', feladat)
    os.makedirs(cel, exist_ok=True)
    ossz = {'be': 0, 'ki': 0, 'ciras': 0, 'colvas': 0}
    jo = rossz = 0
    for sor in nyers.split('\n'):
        if not sor.strip():
            continue
        e = json.loads(sor)
        r = e['result']
        nev = e['custom_id']
        if r['type'] != 'succeeded':
            rossz += 1
            json.dump({'custom_id': nev, 'hiba': r}, open(os.path.join(cel, nev + '.hiba.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
            continue
        u = r['message'].get('usage', {})
        ossz['be'] += u.get('input_tokens', 0)
        ossz['ki'] += u.get('output_tokens', 0)
        ossz['ciras'] += u.get('cache_creation_input_tokens', 0)
        ossz['colvas'] += u.get('cache_read_input_tokens', 0)
        szov = ''.join(b.get('text', '') for b in r['message'].get('content', []) if b.get('type') == 'text')
        lelet = json_ki(szov)
        csonka = r['message'].get('stop_reason') == 'max_tokens'
        if lelet is None or csonka:
            rossz += 1
            open(os.path.join(cel, nev + '.nyers.txt'), 'w', encoding='utf-8').write(szov)
            continue
        jo += 1
        json.dump(lelet, open(os.path.join(cel, nev + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    osszeg = usd(k['modell'], ossz['be'], ossz['ki'], ossz['ciras'], ossz['colvas'])
    if not any(s['koteg'] == k['id'] for s in fokonyv_sorok()):
        uj = not os.path.exists(FOKONYV)
        with open(FOKONYV, 'a', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=FEJ)
            if uj:
                w.writeheader()
            w.writerow({'datum': datetime.date.today().isoformat(), 'feladat': feladat, 'koteg': k['id'], 'modell': k['modell'],
                        'keres': k['keres'], 'sikeres': jo, 'be_token': ossz['be'], 'ki_token': ossz['ki'],
                        'cache_iras_token': ossz['ciras'], 'cache_olvas_token': ossz['colvas'], 'usd': '%.4f' % osszeg})
    print('letolt: %s – használható lelet %d, hibás vagy csonka %d; tényleges költség %.2f USD; a tételsor keretéből maradt %.2f USD'
          % (feladat, jo, rossz, osszeg, keret() - koltott()))


def fokonyv():
    for s in fokonyv_sorok():
        print('%s  %-14s %s  %s kérés  %s USD' % (s['datum'], s['feladat'], s['koteg'], s['keres'], s['usd']))
    print('fokonyv: keret %.2f USD, költve %.2f USD, maradt %.2f USD' % (keret(), koltott(), keret() - koltott()))


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ('keszit', 'kuld', 'allapot', 'letolt', 'fokonyv'):
        sys.exit(__doc__)
    if sys.argv[1] == 'fokonyv':
        return fokonyv()
    if len(sys.argv) < 3 or sys.argv[2] not in FELADATOK:
        sys.exit('Feladat: %s' % ', '.join(FELADATOK))
    {'keszit': keszit, 'kuld': kuld, 'allapot': allapot, 'letolt': letolt}[sys.argv[1]](sys.argv[2])


if __name__ == '__main__':
    main()
