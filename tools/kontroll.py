#!/usr/bin/env python3
"""Szakmai kontroll-kapu: korpusz → IJOTEN → Jogkódex-kommentár, BEKEZDÉSENKÉNT, gépileg ellenőrizve.
(Attila döntése, 2026-11-13: a kontroll nem halasztható, nem szűkíthető mintára, és a lezárást a gép mondja ki,
nem az ügynök. Módosítva: 2026-11-15, folyamataudit „B” változat, Attila jóváhagyása 20:51 – tételszintű alapértékek,
a saját közbenső szöveg gépi lezárása, szűkített kommentár-összegzés, kötelező nyílt forrás a „nem tárgyalja” többletnél.
2026-11-15, 22:31, Attila döntése a próbaköteg után: a magyarázó bekezdésben álló „korpusz” szó nyitott pont.)

    python3 tools/kontroll.py leltar [tétel…]   # a kontroll/NN.json szinkronizálása a tétel jelenlegi szövegével
    python3 tools/kontroll.py kapu  [tétel…]    # ellenőrzés; jelentesek/kontroll_allapot.md (+ .json); kilépési kód 1, ha nyitott
    python3 tools/kontroll.py minta K [mag]     # K véletlen lezárt bekezdés független szúrópróbához
    python3 tools/kontroll.py minta-audit NN [--kihagy id,id,…] [--mag N]
                                                # a tartalmi audit beépített mintája (Attila döntése, 2026-11-15, 21:22)

LELTÁR – kontroll/NN.json
  A tétel MINDEN magyarázó bekezdése (tetel_blokk.blokkok 'p' blokkja) egy bejegyzés. Az azonosító a normalizált szöveg
  lenyomata: ha a bekezdés szövege változik, a régi bejegyzés az „elavult” listába kerül, az új szöveg új, kitöltetlen
  bejegyzést kap – a javított szöveget is újra ellenőrizni kell. Bejegyzést törölni nem lehet; a leltar újra felveszi.
  A korábbi naplók kontroll-listáinak tételei a „lista” részbe kerülnek; mindegyiket bekezdés(ek)hez kell kötni.
  A leltar a fájl minden más felső szintű kulcsát (pl. "alap") változatlanul megőrzi.

  GÉPI LEZÁRÁS (2026-11-15): ha a leltar egy bejegyzést elavulttá tesz, és annak azonosítója a legutóbbi commitban
  (git show HEAD:kontroll/NN.json) sem a „bekezdesek”, sem az „elavult” között nem szerepel – vagyis a szöveg a legutóbbi
  commit óta keletkezett és meg is szűnt (saját közbenső szöveg) –, a leltar maga tölti ki a sorsát:
      "sors": {"dontes": "szerkesztes", "uj": [], "indok": "gépi lezárás: a legutóbbi commit óta keletkezett közbenső szöveg"}
  Ha a git nem érhető el, vagy a fájl a HEAD-ben nincs, a gépi lezárás elmarad (a sorsot kézzel kell kitölteni).
  A kapu ellenőrzi, hogy gépi lezárású bejegyzés a HEAD „bekezdesek” listájában ne szerepeljen (publikált szöveg sorsát
  kézzel kell megírni). A publikált (a HEAD-ben élő) bekezdések elavult bejegyzésének sorsát továbbra is kézzel írod.

TÉTELSZINTŰ ALAPÉRTÉKEK (opcionális, a fájl felső szintjén, a "bekezdesek" mellett):
  "alap": {"ijoten": {"eredmeny": "…", "hely": "…"}, "kommentar_kotet": "a kötet/mű megnevezése és frissítési dátuma",
           "ellenorizte": "…", "datum": "ÉÉÉÉ-HH-NN"}
  A bejegyzésből HIÁNYZÓ "ijoten", "ellenorizte", "datum" mező az alapból öröklődik (a bejegyzésben megadott érték az
  erősebb). Ha a bejegyzés kommentar.hely mezője „#s”-sel kezdődik (pl. "#s14126–#s14128, Ptk. 6:1. §"), a kötet
  megnevezése az alap.kommentar_kotet (ilyenkor ennek kitöltése kötelező). A kapu a tényleges (örökölt) értékkel
  ellenőriz. Alap nélküli fájl a korábbi szabályok szerint érvényes.

BEJEGYZÉS (az ügynök tölti ki):
  tipus      "norma"      – a bekezdés csak azt mondja, amit a megjelölt § szövege (átfogalmazás, összefoglalás)
             "tobblet"    – minden más: fogalom-meghatározás a § szövegén túl, cél, indok, minősítés (pl. jogvesztő,
                            objektív, szubszidiárius), példa, elhatárolás, gyakorlat, szakirodalom, történet, idegen
                            jogi vagy latin megjelölés, uniós háttér, összefoglaló következtetés
             "szerkezeti" – csak átvezető mondat, jogi állítás nélkül (legfeljebb 200 karakter, jelző nélkül)
  korpusz    "Ptk. 6:24. § (2)" – normánál kötelező; a § létezését a kapu ellenőrzi (Ptk.)
  ijoten     {"eredmeny": "egyezik"|"elter"|"nem_targyalja"|"nincs_szocikk", "hely": "szócikk címe, lezárás dátuma"}
             – hiányozhat, ha az alap.ijoten érvényes rá
  kommentar  {"eredmeny": "egyezik"|"elter"|"nem_targyalja", "hely": "kötet/mű, §, #s-horgony" (vagy „#s…”-sel kezdve,
              ha van alap.kommentar_kotet), "osszegzes": "saját szavakkal, mit mond (min. 40 karakter, szó szerinti
              átvétel nélkül)" – csak ott kötelező, ahol az alábbi ÖSSZEGZÉS-szabály előírja}
  megjegyzes eltérésnél kötelező (min. 40 karakter): miért marad így a bekezdés
  bizonytalan true – a bekezdés bizonytalan pontot tartalmaz (a forrás nem egyértelmű, a források eltérnek, vagy csak
             részben igazolják); a jelentés F) pontjában is szerepel. Csak true lehet, vagy el kell hagyni.
  menet      2 – a bekezdést a kétmenetes írás 2. menetében (a kommentár elolvasása után) írták vagy írták át.
             Csak 2 lehet, vagy el kell hagyni (az 1. menet bekezdése nem kap jelet).
  ellenorizte (a tényleges modell nevével, pl. „KP-2 tétel-alügynök (Opus)”), datum – hiányozhat, ha az alapból öröklődik
  Többletnél az IJOTEN ÉS a kommentár is kötelező. Ha egyik sem igazolja és korpusz-§ sincs, a bekezdés nem maradhat:
  javítani vagy törölni kell (ekkor elavul, és az elavult bejegyzés „sors” mezőjét kell kitölteni).
  Elavult bejegyzés: "sors": {"dontes": "javitva"|"torolve"|"szerkesztes", "uj": [új azonosítók], "indok": "…"}
  (min. 10 karakteres indok; az "uj" minden azonosítójának a leltárban kell lennie; gépi lezárásnál "uj": []).

ÖSSZEGZÉS-SZABÁLY (többletnél; 2026-11-15, a 11-13-i részletszabály szűkítése):
  A legalább 40 karakteres kommentar.osszegzes kötelező, ha (i) kommentar.eredmeny == "elter", vagy (ii) a bejegyzés
  "bizonytalan": true, vagy (iii) a bejegyzés jelzői között szerepel a „forras” (gyakorlatra, szakirodalomra utaló
  bekezdés). Egyébként: „egyezik” eredménynél elég, ha a kommentar.hely legalább egy „#s<szám>” horgonyt tartalmaz (ha
  nem tartalmaz, az összegzés ≥ 40 karakter továbbra is kötelező); „nem_targyalja” eredménynél összegzés nem kell, a
  hely (hogy a kötet a tárgyat nem fedi) igen. Megadott összegzés nem ismételheti a bekezdés szövegét.

NYÍLT FORRÁS (KP-2, Attila döntése, 2026-11-14) – a forrássorrend 4. rangja: korpusz → IJOTEN → kommentár → nyílt, hiteles webes forrás.
  nyilt_forras  [{"cim", "kiado", "datum": "ÉÉÉÉ" vagy "ÉÉÉÉ-HH-NN", "url", "hely", "osszegzes" (saját szavakkal, min. 40 karakter),
                  "hatalyossag": {"erintett_par", "par_utolso_modositasa", "eredmeny": "hatalyos"|"reszben_meghaladott"|"nem_hasznalhato"}}]
  Dátum nélküli forrás, tiltott tartomány (blog jellegű és nem hiteles oldalak listája: TILTOTT_FORRAS) hibának számít.
  Érvényes nyílt forrás (eredmény: hatalyos vagy reszben_meghaladott) igazolásnak számít ott, ahol sem az IJOTEN, sem a kommentár
  nem tárgyalja az állítást. Az IJOTEN- és a kommentár-mező kitöltését NEM váltja ki: a többletnél mindkettő továbbra is kötelező
  (ha a tárgynak nincs kommentárkötete: kommentar.eredmeny = "nem_targyalja", a helynél megjelölve, hogy a kötet a tárgyat nem fedi).
  KÖTELEZŐ NYÍLT FORRÁS (2026-11-15; csak a tényleges datum >= "2026-11-16" bejegyzésekre – a korábban lezárt tételek nem
  nyílnak vissza): „többlet” bejegyzésnél, ha kommentar.eredmeny == "nem_targyalja", érvényes nyílt forrás kötelező –
  KIVÉVE, ha a "korpusz" mező a korpuszban lévő előírt iránymutatást nevez meg (PK, PJE, KPJE, PED, „vélemény”,
  „határozat”, „állásfoglalás”), és a "megjegyzes" legalább 40 karakter (miért igazolja az iránymutatás szövege).
  KORPUSZBÓL LEVEZETETT ELHATÁROLÁS (Attila döntése, 2026-11-16, 10:12): a „nem_targyalja” többletnél nyílt forrás akkor
  sem kell, ha a bejegyzés "levezetes": "korpusz" jelet visel, a "korpusz" mező legalább két §-t nevez meg, a "megjegyzes"
  legalább 40 karakter (mely §-ok szövegének összevetéséből következik a bekezdés minden állítása), és a bekezdésnek nincs
  „forras”, „tortenet”, „kulfold” vagy „idegen” jelzője (gyakorlatra, szakirodalomra, történetre, külföldi jogra nem utal).
  KIVÉTEL (Attila döntése, 2026-11-16, 12:25): ha a „forras” vagy a „tortenet” jelzőt a normaszöveg saját fogalma váltja ki
  (pl. a Ptk. 6:63. § (5) „gyakorlat” szava, a 6:87. § (2) „korábbi jognyilatkozatai”), a jel akkor is érvényes, ha a
  bejegyzés "jelzo_indok" mezője legalább 40 karakterben megmondja, melyik § melyik szava váltja ki a jelzőt, és hogy a
  bekezdés bírói gyakorlatra, szakirodalomra, történetre nem utal. A „kulfold” és az „idegen” jelzőre nincs kivétel.
  A jelet csak a központi chat adhatja, a bekezdés minden mondatának a megnevezett §-okból való ellenőrzése után.

BŐVÍTÉSI LISTA – kontroll/_bovites.json: [{"tetel", "forras", "targy", "kommentar_hely", "allapot": "nyitott"|"potolva"|"nem_kell",
                                         "datum", "kotelezo": true|false}]
  A kommentár által megjelölt, a korpuszban nem szereplő elsődleges források. AJÁNLÁS (Attila döntése, 2026-11-14): a tételsor
  ezek nélkül is teljes; ha Attila a korpuszba teszi őket, a tétel név szerint is feldolgozza a döntést. A kapu a
  jelentesek/bovitesi_lista.md-be írja, de NEM blokkol. Kivétel: "kotelezo": true – a hivatalos tételsor által előírt, a
  korpuszból hiányzó forrás; ilyen nyitott tétel esetén a teljes futás 1-es kilépési kódot ad.

AUDIT-MINTA (2026-11-15, 21:22) – a köteg végi szúrópróba helyett a tartalmi audit-alügynök tételenként gépi mintát vesz
  azokból a „többlet” bekezdésekből, amelyeket a célzott audit egyébként NEM nyitna meg: minta-audit NN --kihagy <a már
  megnyitott bekezdések azonosítói>. A minta mérete: 5, de legalább a szóba jöhető többlet-bekezdések 10%-a (felfelé
  kerekítve); a mag alapértéke a tétel száma (ugyanarra a bemenetre ugyanaz a minta). A mintát a gép húzza, nem az ügynök.

SZÚRÓPRÓBA – kontroll/_minta.json: [{"tetel", "id", "ellenorizte", "eredmeny": "megerosit"|"cafol", "indok"}]
  Cáfolt bejegyzés a tételt visszanyitja, amíg a bejegyzés újra nincs kitöltve (dátuma a cáfolatnál későbbi).
"""
import datetime, hashlib, json, os, random, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kozos
import tetel_blokk

DIR = os.path.join(kozos.GYOKER, 'kontroll')
JEL = os.path.join(kozos.GYOKER, 'jelentesek')
MINTA = os.path.join(DIR, '_minta.json')
HIANY = os.path.join(DIR, '_bovites.json')
HAT = {'hatalyos', 'reszben_meghaladott', 'nem_hasznalhato'}
TILTOTT_FORRAS = ('wikipedia.org', 'mersz.hu', 'facebook.com', 'reddit.com', 'gyakorikerdesek.hu', 'chatgpt.com', 'openai.com',
                  'claude.ai', 'gemini.google.com', 'perplexity.ai', 'quora.com', 'medium.com', 'blog.')

# Jelzők. KOTELEZO_TOBBLET: ezek a bekezdések nem lehetnek „norma” vagy „szerkezeti”.
# A minták a beállítás kontroll.jelzok mezőjéből jönnek (A/1: régi Ptk, 1959, PK, PJE …).
JELZOK = kozos.beallitas()['kontroll']['jelzok']
KOTELEZO_TOBBLET = {'forras', 'tortenet', 'kulfold', 'minosites', 'idegen'}
IJ = {'egyezik', 'elter', 'nem_targyalja', 'nincs_szocikk'}
KO = {'egyezik', 'elter', 'nem_targyalja'}
GEPI_INDOK = 'gépi lezárás: a legutóbbi commit óta keletkezett közbenső szöveg'
NYILT_KOTELEZO_DATUM = '2026-11-16'   # a kötelező nyílt forrás szabálya ettől a (tényleges) dátumtól él
IRANYMUTATAS_RX = kozos.beallitas()['kontroll']['iranymutatasRx']
ORO = ('ijoten', 'ellenorizte', 'datum')   # az alapból öröklődő mezők


def lenyomat(s):
    return hashlib.sha1(kozos.norm(s).encode('utf-8')).hexdigest()[:12]


KIHAGYOTT_TERMEK = []   # a még le nem gyártott termékek (tetel_blokk): az ellenőrzésük kimarad, figyelmeztetéssel (KE-3/6)


def bekezdesek(n):
    """[(id, szakasz, szöveg)] a tétel magyarázó bekezdéseire; azonos szövegnél sorszám-utótag. Ha a tétel terméke
    (termekek/paragrafus_jegyzek, termekek/hangos_vazlat) még nincs legyártva, a termékre vonatkozó ellenőrzés kimarad
    (KIHAGYOTT_TERMEK; a kapu és a leltar figyelmeztet); a bekezdések és a szakmai kontroll ettől függetlenek."""
    out, lat, fo = [], {}, ''
    kih = []
    blokk = tetel_blokk.blokkok(n, kih)
    for k in kih:
        if k not in KIHAGYOTT_TERMEK:
            KIHAGYOTT_TERMEK.append(k)
    for b in blokk:
        if b[0] == 'f':
            fo = b[1]
        if b[0] != 'p':
            continue
        h = lenyomat(b[1]); lat[h] = lat.get(h, 0) + 1
        out.append((h if lat[h] == 1 else f'{h}-{lat[h]}', fo, b[1]))
    return out


def jelzok(s):
    return sorted(k for k, rx in JELZOK.items() if re.search(rx, s, re.I if k not in ('idegen', 'forras') else 0))


# ---- a korábbi naplók kontroll-listái ----
def tagol(s, rx):
    """Szétválasztás az rx határolón, de zárójelen és *…* jelölésen belül nem."""
    out, cur, m = [], '', 0
    i = 0
    while i < len(s):
        mm = re.compile(rx).match(s, i)
        if mm and m == 0 and mm.end() > i:
            out.append(cur); cur = ''; i = mm.end(); continue
        c = s[i]; m += (c == '(') - (c == ')'); cur += c; i += 1
    out.append(cur)
    return out


def lista_tetelek():
    out = {}

    def tesz(n, szoveg, forras):
        szoveg = szoveg.strip(' .;')
        if len(szoveg) > 8 and 'kérlek' not in szoveg:
            out.setdefault(n, []).append({'allitas': szoveg, 'forras': forras})

    for fn in ('szakmai_B_kor.md', 'szakmai_C_kor.md', 'dobozok_12_14_20.md'):
        p = os.path.join(JEL, fn)
        if not os.path.exists(p):
            continue
        akt = None; L = open(p, encoding='utf-8').read().split('\n'); i = 0
        while i < len(L):
            l = L[i]
            m = re.match(r'^## (\d+)\. tétel', l)
            if m:
                akt = int(m.group(1))
            elif l.startswith('## '):
                akt = None
            if re.search(r'Kontroll-lista', l):
                torzs = (l.split(':', 1)[1] if ':' in l else '').strip()
                torzs = re.split(r'\s*Megjegyzés:', torzs)[0]
                j = i + 1; pontok = []
                while j < len(L) and re.match(r'^\s+- ', L[j]):
                    pontok.append(L[j].strip()[2:]); j += 1
                if pontok and akt:
                    for d in pontok:
                        tesz(akt, d, fn)
                    i = j; continue
                darabok = re.split(r'(?:^|;\s*)(\d+)\. tétel\s*[–-]\s*', torzs)
                if len(darabok) > 1:
                    for k in range(1, len(darabok), 2):
                        for d in tagol(darabok[k + 1], r';\s*|, (?=a |az |„)'):
                            tesz(int(darabok[k]), d, fn)
                elif akt:
                    for d in tagol(torzs, r';\s*'):
                        tesz(akt, d, fn)
                i = j; continue
            i += 1
    return out


def betolt(n):
    p = os.path.join(DIR, f'{n:02d}.json')
    if os.path.exists(p):
        return json.load(open(p, encoding='utf-8'))
    return {'tetel': n, 'bekezdesek': [], 'elavult': [], 'lista': []}


def ment(n, d):
    os.makedirs(DIR, exist_ok=True)
    with open(os.path.join(DIR, f'{n:02d}.json'), 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=1); f.write('\n')


def head_fajl(n):
    """A kontroll/NN.json a legutóbbi commitban (dict), vagy None, ha a git nem érhető el vagy a fájl nincs a HEAD-ben."""
    try:
        r = subprocess.run(['git', '-C', kozos.GYOKER, 'show', f'HEAD:kontroll/{n:02d}.json'],
                           capture_output=True, timeout=30)
    except Exception:
        return None
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout.decode('utf-8'))
    except Exception:
        return None


def tenyleges(b, alap):
    """A bejegyzés tényleges értékei: a hiányzó ijoten/ellenorizte/datum az alapból, a „#s”-sel kezdődő
    kommentárhely elé az alap.kommentar_kotet kerül. Másolatot ad; az eredeti bejegyzést nem módosítja."""
    if not alap:
        return b
    t = dict(b)
    for k in ORO:
        if k not in t and k in alap:
            t[k] = alap[k]
    ko = t.get('kommentar')
    if isinstance(ko, dict) and str(ko.get('hely', '')).startswith('#s') and alap.get('kommentar_kotet'):
        ko = dict(ko); ko['hely'] = f"{alap['kommentar_kotet']}, {ko['hely']}"; t['kommentar'] = ko
    return t


def termek_figyelmeztetes():
    """„termék nincs legyártva – kihagyva” (stderr), ha a tetel_blokk termék-ellenőrzése valamely tételnél kimaradt; a
    sor a kimenet ÁLLAPOT-sorát nem érinti. Vissza: a figyelmeztetés szövege vagy ''."""
    if not KIHAGYOTT_TERMEK:
        return ''
    mappak = sorted({os.path.dirname(k) for k in KIHAGYOTT_TERMEK})
    db = len({os.path.basename(k) for k in KIHAGYOTT_TERMEK})
    s = 'figyelmeztetés: termék nincs legyártva – kihagyva (%s; %d tétel): a termékre vonatkozó ellenőrzés kimaradt, a szakmai kontroll állapota ettől független' % (', '.join(m + '/' for m in mappak), db)
    sys.stderr.write(s + '\n')
    return s


def leltar(ns):
    lt = lista_tetelek(); uj_db = el_db = gepi_db = 0
    for n in ns:
        d = betolt(n); regi = {b['id']: b for b in d['bekezdesek']}
        head = head_fajl(n)
        head_ids = None if head is None else {b.get('id') for b in head.get('bekezdesek', []) + head.get('elavult', [])}
        cur = bekezdesek(n); ids = {i for i, _, _ in cur}; uj = []
        for i, fo, s in cur:
            b = regi.get(i) or {'id': i, 'tipus': None}
            if i not in regi:
                uj_db += 1
            b.update({'szakasz': fo, 'kezdet': s[:90], 'hossz': len(s), 'jelzok': jelzok(s)})
            uj.append(b)
        for i, b in regi.items():
            if i not in ids:
                b.setdefault('elavult_datum', datetime.date.today().isoformat())
                if head_ids is not None and i not in head_ids and not b.get('sors'):
                    b['sors'] = {'dontes': 'szerkesztes', 'uj': [], 'indok': GEPI_INDOK}; gepi_db += 1
                d['elavult'].append(b); el_db += 1
        d['bekezdesek'] = uj
        meglevo = {x['allitas'] for x in d['lista']}
        for x in lt.get(n, []):
            if x['allitas'] not in meglevo:
                d['lista'].append({**x, 'bekezdesek': []})
        ment(n, d)
    termek_figyelmeztetes()
    print(f'leltár: {len(ns)} tétel; új bejegyzés: {uj_db}; elavult: {el_db} (ebből gépi lezárás: {gepi_db})')


# ---- kapu ----
def ptk_parok():
    """{forráskód: a korpuszban meglévő egységek (§ vagy cikk) halmaza} MINDEN tagolt forrásra, amelynek korpuszfájlja
    van (kozos.forrasok() / kozos.korpusz_jogszabalyok(); KE-3/6), nem csak a kontroll.paragrafusForrasok forrásaira –
    kódonként, nem a halmazok uniója (a Szabs. tv. §-át a Bv. tv. azonos számú §-a nem „igazolja”); a cikkre tagolt
    forrás a cikkeit adja (nem üres halmazt). A paragrafusForrasok forrása elöl áll (a rövidítés nélküli „12. §” gazdája
    közülük kerül ki)."""
    try:
        J = kozos.korpusz_jogszabalyok()
        pf = list(kozos.beallitas()['kontroll']['paragrafusForrasok'])
        ki = {kod: set(J.get(kod, ({}, []))[0]) for kod in pf}
        for kod, (d, _) in J.items():
            if kod not in ki:
                ki[kod] = set(d)
        return ki
    except Exception:
        return None


def _rov_minta(kod):
    """A forrás rövidítéseinek mintája a dobozRovidites alapján (a korpusz-mező hivatkozásaihoz)."""
    return '|'.join(r for r, k in kozos.DOBOZ_RÖVIDITES if k == kod) or re.escape(kod)


def _egyseg_minta(kod):
    """A forrás egységének mintája a saját számozása szerint: könyves § („3:123. §”), egyszerű § („12. §”, „36/D. §”),
    cikk („288. cikk”, „4a. cikk”), római vagy betűs cikk („XXVIII. cikk”, „T) cikk”)."""
    if kozos.egyseg(kod) == '§':
        return r'(\d+(?::\d+)?(?:/[A-Z])?)\.\s?§'
    return r'(\d+[a-z]?|[IVXLC]+|[A-Z]\))\.?\s?[Cc]ikk'


def korpusz_hivatkozasok(k, ptk):
    """A norma korpusz-mezőjének egységhivatkozásai: [(forráskód, egység, megnevezés)]. Kódonkénti minta, a hivatkozott
    forrás saját egysége és számozása szerint (KE-3/6): „Ptk. 6:24. §”, „Ctv. 9. §”, „EUMSZ 288. cikk”, „Alaptörvény
    XXVIII. cikk”, „GDPR 5. cikk”; a rövidítés nélküli „12. §” a fő kódexé (ha az a paragrafusForrasok között van),
    különben az egyetlen paragrafusForrasé. A hosszabb rövidítés előbb illeszkedik („Módosított Ptk.” a „Ptk.” előtt)."""
    ki, hasznalt = [], []
    rov = sorted(((len(r), r, kod) for r, kod in kozos.DOBOZ_RÖVIDITES if kod in ptk), reverse=True)
    rov += [(len(kod), re.escape(kod), kod) for kod in ptk if not any(k2 == kod for _, _, k2 in rov)]
    for _, r, kod in rov:
        for m in re.finditer(r'(?<![\w.])(?:%s)\s*%s' % (r, _egyseg_minta(kod)), k):
            if any(a <= m.start() < b for a, b in hasznalt):
                continue      # a hosszabb rövidítés már lefedte („Módosított Ptk. 6:550. §”)
            ki.append((kod, m.group(1), m.group(0)))
            hasznalt.append(m.span())
    # más forrás rövidítésével álló egység („Ptk. 3:1. §” a B/3-ban, „Kp. 12. §” az A/3-ban) nem a fő kódexé
    for m in re.finditer(r'(?:%s|\b[A-ZÁÉÍÓÖŐÚÜŰ][\wáéíóöőúüű]*\.(?:\s?tv\.)?)\s*\d+(?::\d+)?(?:/[A-Z])?\.\s?§'
                         % '|'.join(r for r, _ in kozos.DOBOZ_RÖVIDITES), k):
        hasznalt.append(m.span())
    maradek = ''.join(' ' if any(a <= i < b for a, b in hasznalt) else c for i, c in enumerate(k))
    fo = kozos.beallitas()['foKodex']
    pf = kozos.beallitas()['kontroll']['paragrafusForrasok']
    alap = fo if fo in ptk and fo in pf else (pf[0] if len(pf) == 1 and pf[0] in ptk else None)
    if alap:
        rx = r'(?<![\d:/])(\d+(?::\d+)?(?:/[A-Z])?)\.\s?§' if kozos.egyseg(alap) == '§' else r'(?<![\w)])(\d+[a-z]?|[IVXLC]+|[A-Z]\))\.?\s?[Cc]ikk'
        for m in re.finditer(rx, maradek):
            if kozos.konyves(alap) and ':' not in m.group(1):
                continue      # a könyves fő kódex (Ptk.) egysége csak „könyv:§” lehet; a puszta „12. §” nem az övé
            ki.append((alap, m.group(1), m.group(0)))
    return ki


def nyilt_forras_hibak(b):
    """([hibák], van-e érvényes, hatályosságra ellenőrzött nyílt forrás)."""
    h, ervenyes = [], False
    for i, f in enumerate(b.get('nyilt_forras') or [], 1):
        e = []
        if not isinstance(f, dict):
            h.append(f'nyílt forrás {i}: hibás szerkezet'); continue
        for k in ('cim', 'kiado', 'hely'):
            if len(str(f.get(k) or '')) < 3:
                e.append(f'hiányzik: {k}')
        if not re.fullmatch(r'(19|20)\d\d(-\d\d(-\d\d)?)?', str(f.get('datum') or '')):
            e.append('a forrás dátuma hiányzik vagy hibás (dátum nélküli forrás nem használható)')
        u = str(f.get('url') or '')
        if not u.startswith('http'):
            e.append('hiányzik: url')
        elif any(t in u.lower() for t in TILTOTT_FORRAS):
            e.append('nem hiteles forrás (tiltott tartomány)')
        if len(str(f.get('osszegzes') or '')) < 40:
            e.append('az összegzés hiányzik vagy 40 karakternél rövidebb')
        elif kozos.norm(f['osszegzes'])[:60] in kozos.norm(b.get('kezdet', '')):
            e.append('az összegzés a bekezdés szövegét ismétli')
        ht = f.get('hatalyossag') or {}
        if ht.get('eredmeny') not in HAT or len(str(ht.get('erintett_par') or '')) < 3 or len(str(ht.get('par_utolso_modositasa') or '')) < 4:
            e.append('a hatályossági vizsgálat hiányzik (érintett §, a § utolsó módosítása, eredmény)')
        if e:
            h.append(f'nyílt forrás {i}: ' + '; '.join(e))
        elif ht.get('eredmeny') != 'nem_hasznalhato':
            ervenyes = True
    return h, ervenyes


def nyilt_hiany(b, nyilt_ok):
    """Igaz, ha a (tényleges) többlet-bejegyzés a kötelező nyílt forrás szabályán bukik (a dátumtól függetlenül)."""
    if b.get('tipus') != 'tobblet' or (b.get('kommentar') or {}).get('eredmeny') != 'nem_targyalja' or nyilt_ok:
        return False
    if re.search(IRANYMUTATAS_RX, str(b.get('korpusz') or '')) and len(str(b.get('megjegyzes') or '')) >= 40:
        return False
    return not korpusz_levezetes(b)


def korpusz_levezetes(b):
    """Korpuszból levezetett elhatárolás (Attila döntése, 2026-11-16, 10:12): "levezetes": "korpusz", legalább két
    megnevezett korpusz-§, legalább 40 karakteres megjegyzés, és a bekezdés nem utal gyakorlatra, szakirodalomra,
    történetre, külföldi jogra vagy idegen megjelölésre. A „forras” és a „tortenet” jelző nem akadály, ha legalább
    40 karakteres "jelzo_indok" megmondja, hogy a jelzőt a normaszöveg saját fogalma váltja ki (2026-11-16, 12:25)."""
    return (b.get('levezetes') == 'korpusz' and len(re.findall(r'§', str(b.get('korpusz') or ''))) >= 2
            and len(str(b.get('megjegyzes') or '')) >= 40
            and not (set(b.get('jelzok', [])) & ({'kulfold', 'idegen'} if len(str(b.get('jelzo_indok') or '')) >= 40
                                                 else {'forras', 'tortenet', 'kulfold', 'idegen'})))


def hiany_lista():
    return json.load(open(HIANY, encoding='utf-8')) if os.path.exists(HIANY) else []


def hiba_bejegyzes(b, ptk, alap=None):
    h = []
    if alap and str((b.get('kommentar') or {}).get('hely', '')).startswith('#s') and len(str(alap.get('kommentar_kotet') or '')) < 5:
        h.append('a kommentár helye „#s”-sel kezdődik, de az alap.kommentar_kotet hiányzik')
    b = tenyleges(b, alap)
    t = b.get('tipus'); jz = set(b.get('jelzok', []))
    if t not in ('norma', 'tobblet', 'szerkezeti'):
        return h + ['nincs besorolva']
    if 'bizonytalan' in b and b['bizonytalan'] is not True:
        h.append('a „bizonytalan” mező csak true lehet (vagy el kell hagyni)')
    if 'levezetes' in b and b['levezetes'] != 'korpusz':
        h.append('a „levezetes” mező csak "korpusz" lehet (vagy el kell hagyni)')
    if 'menet' in b and b['menet'] != 2:
        h.append('a „menet” mező csak 2 lehet (vagy el kell hagyni)')
    if t == 'szerkezeti' and (jz or b.get('hossz', 0) > 200):
        h.append('szerkezetinek jelölve, de jelzője van vagy 200 karakternél hosszabb')
    if t == 'norma':
        if jz & KOTELEZO_TOBBLET:
            h.append('normának jelölve, de jelzője miatt többlet: ' + ', '.join(sorted(jz & KOTELEZO_TOBBLET)))
        k = b.get('korpusz') or ''
        if not re.search(r'§|\b[Cc]ikk\b', k):
            h.append('normánál a korpusz-§ (cikkre tagolt forrásnál a cikk) kötelező')
        elif ptk is not None:
            for kod, p, nev in korpusz_hivatkozasok(k, ptk):
                if p not in ptk[kod]:
                    h.append(f'a {kod} {nev.strip()} nincs a korpuszban')
    if t == 'tobblet':
        ij = b.get('ijoten') or {}; ko = b.get('kommentar') or {}
        if ij.get('eredmeny') not in IJ or len(ij.get('hely', '')) < 5:
            h.append('IJOTEN-ellenőrzés hiányzik (eredmény + hely)')
        if ko.get('eredmeny') not in KO or len(ko.get('hely', '')) < 5:
            h.append('kommentár-ellenőrzés hiányzik (eredmény + hely)')
        else:
            osz = str(ko.get('osszegzes') or '')
            kell = ko.get('eredmeny') == 'elter' or b.get('bizonytalan') is True or 'forras' in jz
            if not kell and ko.get('eredmeny') == 'egyezik' and not re.search(r'#s\d+', ko.get('hely', '')):
                kell = True   # #s-horgony nélkül az „egyezik” eredményhez az összegzés továbbra is kell
            if kell and len(osz) < 40:
                h.append('a kommentár összegzése hiányzik vagy 40 karakternél rövidebb'
                         ' (kötelező: eltérésnél, bizonytalan pontnál, gyakorlatra utaló bekezdésnél, #s-horgony nélküli egyezésnél)')
            elif len(osz) >= 40 and kozos.norm(osz)[:60] in kozos.norm(b.get('kezdet', '')):
                h.append('a kommentár összegzése a bekezdés szövegét ismétli')
        if 'elter' in (ij.get('eredmeny'), ko.get('eredmeny')) and len(b.get('megjegyzes', '')) < 40:
            h.append('eltérésnél a megjegyzés kötelező (miért marad így)')
        nh, nyilt_ok = nyilt_forras_hibak(b)
        h += nh
        if ij.get('eredmeny') in ('nem_targyalja', 'nincs_szocikk', None) and ko.get('eredmeny') == 'nem_targyalja' and '§' not in (b.get('korpusz') or '') and not nyilt_ok:
            h.append('nem igazolt állítás: sem IJOTEN, sem kommentár, sem korpusz-§, sem érvényes nyílt forrás – javítani vagy törölni kell')
        if nyilt_hiany(b, nyilt_ok) and str(b.get('datum') or '') >= NYILT_KOTELEZO_DATUM:
            h.append('a kommentár a tárgyat nem tárgyalja: érvényes nyílt forrás kötelező (vagy a korpusz-mezőben előírt '
                     'iránymutatás és legalább 40 karakteres megjegyzés)')
    if not b.get('ellenorizte') or not b.get('datum'):
        h.append('ellenőrző és dátum hiányzik')
    return h


def kapu(ns, ir=True):
    ptk = ptk_parok()
    minta = json.load(open(MINTA, encoding='utf-8')) if os.path.exists(MINTA) else []
    cafol = {}
    for m in minta:
        if m.get('eredmeny') == 'cafol':
            cafol[(m['tetel'], m['id'])] = m.get('datum', '')
    sorok = []; ossz = {'tetel': len(ns), 'lezart': 0, 'bekezdes': 0, 'kesz': 0, 'tobblet': 0, 'norma': 0, 'szerkezeti': 0, 'elter': 0}
    reszlet = []
    for n in ns:
        if not os.path.isfile(os.path.join(kozos.GYOKER, f'{n:02d}.txt')):
            sorok.append(f'| {n}. | NYITOTT | 0/0 | 0 / 0 | 0 | 1 |')
            reszlet.append(f'### {n}. tétel – 1 nyitott pont\n\n- nincs tételszöveg')
            continue
        d = betolt(n); cur = {i for i, _, _ in bekezdesek(n)}; hibak = []; alap = d.get('alap') or None
        if 'alap' in d and not isinstance(d['alap'], dict):
            hibak.append('az „alap” kulcs nem objektum'); alap = None
        if not d['bekezdesek']:
            hibak.append('nincs leltár (futtasd: kontroll.py leltar)')
        nyilv = {b['id'] for b in d['bekezdesek']}
        if cur != nyilv:
            hibak.append(f'a leltár nem egyezik a tétel szövegével ({len(cur - nyilv)} új, {len(nyilv - cur)} elavult bekezdés) – futtasd a leltart')
        for bi, _, bsz in bekezdesek(n):
            if re.search(r'\bkorpusz', bsz, re.I):  # 2026-11-15, 22:31 (Attila döntése): belső munkaszó a tételszövegben
                hibak.append(f'{bi}: a tételszövegben a „korpusz” szó áll (belső munkaszó; a forrást nevén kell nevezni)')
        kesz = 0
        for b in d['bekezdesek']:
            h = hiba_bejegyzes(b, ptk, alap)
            c = cafol.get((n, b['id']))
            if c is not None and not (str(tenyleges(b, alap).get('datum') or '') > c):
                h.append('szúrópróbán cáfolva, újra kell ellenőrizni')
            if h:
                hibak.append(f"{b['id']} „{b.get('kezdet', '')[:50]}…”: " + '; '.join(h))
            else:
                kesz += 1
            ossz[b.get('tipus')] = ossz.get(b.get('tipus'), 0) + (1 if b.get('tipus') in ('tobblet', 'norma', 'szerkezeti') else 0)
            if 'elter' in ((b.get('ijoten') or {}).get('eredmeny'), (b.get('kommentar') or {}).get('eredmeny')):
                ossz['elter'] += 1
        head_el = None
        if any((b.get('sors') or {}).get('indok') == GEPI_INDOK for b in d['elavult']):
            head = head_fajl(n)
            head_el = None if head is None else {b.get('id') for b in head.get('bekezdesek', [])}
        for b in d['elavult']:
            s = b.get('sors') or {}
            if s.get('indok') == GEPI_INDOK and head_el is not None and b['id'] in head_el:
                hibak.append(f"elavult {b['id']}: gépi lezárás publikált (a legutóbbi commitban élő) bekezdésen – a sorsot kézzel kell megírni")
            if s.get('dontes') not in ('javitva', 'torolve', 'szerkesztes') or len(s.get('indok', '')) < 10:
                hibak.append(f"elavult {b['id']}: a sors (javitva/torolve/szerkesztes + indok) nincs kitöltve")
            for u in s.get('uj', []):
                if u not in nyilv:
                    hibak.append(f"elavult {b['id']}: az új azonosító ({u}) nincs a leltárban")
        for x in d['lista']:
            if not x.get('bekezdesek') or any(i not in nyilv for i in x['bekezdesek']):
                hibak.append(f"kontroll-lista „{x['allitas'][:60]}…”: nincs érvényes bekezdéshez kötve")
        ossz['bekezdes'] += len(d['bekezdesek']); ossz['kesz'] += kesz
        lez = not hibak
        ossz['lezart'] += lez
        tb = sum(1 for b in d['bekezdesek'] if b.get('tipus') == 'tobblet'); nb = sum(1 for b in d['bekezdesek'] if b.get('tipus') == 'norma')
        figy = ' ⚠ kevés többlet (távirat-gyanú) – mérce-szúrópróba javasolt' if lez and nb + tb and tb / (nb + tb) < 0.25 else ''
        sorok.append(f"| {n}. | {'LEZÁRVA' if lez else 'NYITOTT'} | {kesz}/{len(d['bekezdesek'])} | {nb} / {tb} | {len(d['lista'])} | {len(hibak)}{figy} |")
        if hibak:
            reszlet.append(f'### {n}. tétel – {len(hibak)} nyitott pont\n\n' + '\n'.join('- ' + h for h in hibak[:40]) + (f'\n- … és még {len(hibak) - 40}' if len(hibak) > 40 else ''))
    nyitott = ossz['tetel'] - ossz['lezart']
    hl = [x for x in hiany_lista() if x.get('tetel') in ns]
    hny = [x for x in hl if x.get('allapot', 'nyitott') == 'nyitott']
    hkot = [x for x in hny if x.get('kotelezo')]
    ossz['bovites'] = len(hl); ossz['bovites_nyitott'] = len(hny); ossz['hianylista_nyitott'] = len(hkot)
    hsor = f"BŐVÍTÉSI LISTA (ajánlás, nem feltétele a lezárásnak): {len(hny)} nyitott forrás, {len(hl)} összesen."
    if hkot:
        hsor += f" ELŐÍRT FORRÁS HIÁNYZIK A KORPUSZBÓL: {len(hkot)} – a tételsor addig nem élesíthető."
    fej = [
        '# Szakmai kontroll – állapot (gépi jelentés, kézzel nem szerkeszthető)',
        '',
        f"**ÁLLAPOT: {ossz['lezart']}/{ossz['tetel']} tétel lezárva; {ossz['kesz']}/{ossz['bekezdes']} bekezdés ellenőrizve; "
        f"eltérés: {ossz['elter']}.**" + (f' **{nyitott} tétel NYITOTT – ezekre épülő termék és hang nem tekinthető ellenőrzöttnek.**' if nyitott else ' Minden tétel lezárva.'),
        '',
        f"Generálta: `tools/kontroll.py kapu`, {datetime.datetime.now().isoformat(timespec='minutes')}. Sorrend: korpusz → IJOTEN → Jogkódex-kommentár; a lezárást a kapu mondja ki.",
        '',
        '| Tétel | Állapot | Kész bekezdés | Norma / többlet | Kontroll-lista | Nyitott pont |',
        '|---|---|---|---|---|---|',
    ]
    figy_termek = termek_figyelmeztetes()
    if figy_termek:
        fej[6:6] = [figy_termek, '']
    if ir and len(ns) == len(kozos.tetelsor()['tetelek']):
        with open(os.path.join(JEL, 'kontroll_allapot.md'), 'w', encoding='utf-8') as f:
            f.write('\n'.join(fej + sorok) + '\n\n## Nyitott pontok\n\n' + ('\n\n'.join(reszlet) or 'nincs') + '\n')
        with open(os.path.join(JEL, 'kontroll_allapot.json'), 'w', encoding='utf-8') as f:
            json.dump(ossz, f, ensure_ascii=False, indent=1); f.write('\n')
        with open(os.path.join(JEL, 'bovitesi_lista.md'), 'w', encoding='utf-8') as f:
            f.write('# Bővítési lista (gépi jelentés a kontroll/_bovites.json-ból, kézzel nem szerkeszthető)\n\nA kommentár által megjelölt, a korpuszban nem szereplő források. Ajánlás: a tételek ezek nélkül is teljesek; ha a forrás a korpuszba kerül, a tétel név szerint is feldolgozza.\n\n' + hsor + '\n\n'
                    '| Tétel | Forrás | Tárgy | A kommentár helye | Állapot | Előírt? |\n|---|---|---|---|---|---|\n'
                    + '\n'.join(f"| {x.get('tetel')}. | {x.get('forras', '')} | {x.get('targy', '')} | {x.get('kommentar_hely', '')} | {x.get('allapot', 'nyitott')} | {'igen' if x.get('kotelezo') else 'nem'} |" for x in hl) + '\n')
    print(fej[2].replace('**', ''))
    print(hsor)
    if len(ns) < 10:
        for r in reszlet:
            print(r[:3000])
    return ossz


def osszegzes():
    """Rövid állapot más eszközöknek (csomag_gyart): {'tetel', 'lezart', ...}; a jelentést nem írja."""
    return kapu([t['sorszam'] for t in kozos.tetelsor()['tetelek']], ir=False)


def mintavetel(k, mag):
    rnd = random.Random(mag); pool = []
    for t in kozos.tetelsor()['tetelek']:
        n = t['sorszam']
        d = betolt(n)
        for b in d['bekezdesek']:
            b = tenyleges(b, d.get('alap'))
            if b.get('tipus') in ('tobblet', 'norma') and b.get('datum'):
                pool.append((n, b))
    for n, b in rnd.sample(pool, min(k, len(pool))):
        print(f"{n}. tétel  {b['id']}  [{b['tipus']}]  {b.get('korpusz', '')}\n   „{b['kezdet']}…”\n   kommentár: {(b.get('kommentar') or {}).get('hely', '–')}\n")


def minta_audit(n, kihagy, mag):
    """A tartalmi audit beépített mintája: az n. tétel „többlet” bekezdései közül, a kihagyottak nélkül."""
    d = betolt(n); pool = []
    for b in d['bekezdesek']:
        if b.get('tipus') == 'tobblet' and b['id'] not in kihagy:
            pool.append(tenyleges(b, d.get('alap')))
    k = min(len(pool), max(5, -(-len(pool) // 10)))
    valasztott = random.Random(mag).sample(sorted(pool, key=lambda b: b['id']), k)
    print(f"{n}. tétel – audit-minta: {k} bekezdés a {len(pool)} szóba jöhető többlet-bekezdésből (kihagyva: {len(kihagy)}; mag: {mag})")
    for b in valasztott:
        print(f"{b['id']}  {b.get('korpusz', '')}\n   „{b['kezdet']}…”\n   kommentár: {(b.get('kommentar') or {}).get('hely', '–')}")


if __name__ == '__main__':
    if len(sys.argv) >= 3 and sys.argv[1] == 'minta-audit':
        arg = sys.argv[3:]; kih = set(); mg = int(sys.argv[2])
        if '--kihagy' in arg:
            kih = {x for x in arg[arg.index('--kihagy') + 1].split(',') if x}
        if '--mag' in arg:
            mg = int(arg[arg.index('--mag') + 1])
        minta_audit(int(sys.argv[2]), kih, mg); sys.exit(0)
    if len(sys.argv) < 2 or sys.argv[1] not in ('leltar', 'kapu', 'minta'):
        print(__doc__); sys.exit(2)
    mind = [t['sorszam'] for t in kozos.tetelsor()['tetelek']]
    if sys.argv[1] == 'minta':
        mintavetel(int(sys.argv[2]), int(sys.argv[3]) if len(sys.argv) > 3 else 0); sys.exit(0)
    ns = [int(x) for x in sys.argv[2:]] or mind
    if sys.argv[1] == 'leltar':
        leltar(ns)
    else:
        o = kapu(ns)
        sys.exit(0 if o['lezart'] == o['tetel'] and not (len(ns) == len(mind) and o['hianylista_nyitott']) else 1)
