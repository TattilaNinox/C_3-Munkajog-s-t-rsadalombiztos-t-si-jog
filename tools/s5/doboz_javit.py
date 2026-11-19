#!/usr/bin/env python3
"""S3: a jogszabálydobozok újraépítése a korpuszból – teljes bekezdésekkel, betűre. A §-os és a cikkre tagolt
forrás dobozára is (a forrás egysége a beállításból: kozos.egyseg; a bekezdésszerkezet a korpuszfájl soraiból).
Használat (a tárolóból): python3 tools/s5/doboz_javit.py [--sor] [--diff] [--ir] [tétel ...]
A doboz által érintett bekezdéseket (és a szögletes címet, ha a dobozban volt) a korpusz
sorrendjében, a korpusz soraiból írja újra; csak ott módosít, ahol a doboz eltér.
Idempotens (KE-2): a korpusz sorait a dobozfelismerő (kozos.dobozok) szabálya szerint tördeli (tordel), a beírt dobozt
visszaolvasva ellenőrzi (elemez), a doboz után álló, a cikk szövegét folytató sorokat a dobozhoz veszi (folytatas); a
második futás ezért nem talál módosítandó dobozt. A preambulumbekezdés doboza nem épül újra (a bekezdéshatár a kétoszlopos
korpuszban nem állapítható meg).
"""
import os, re, sys, difflib
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kozos

IR = '--ir' in sys.argv
TETELEK = [int(a) for a in sys.argv[1:] if a.isdigit()]
F = kozos.forrasok()


def csillagtalan(l):
    l = kozos.nfc(l).replace(' ', ' ')
    l = re.sub(r'\s*\*(?=\s|$)', '', l)
    return re.sub(r'[ \t]+', ' ', l).strip()


def cimsor(l):
    if l.startswith('['):
        return False
    if re.match(r'^\(\d+[a-z]?\)', l) or re.match(r'^[a-z]{1,2}\) ', l):
        return False
    if re.fullmatch(r'\d+(?::\d+)?(?:/[A-Z])?\.', l):
        return True      # a következő alcím puszta sorszáma („133/C. *”)
    return not re.search(r'[.;:,]$', l) or (l.isupper() and len(l) > 3)


_CACHE = {}
CSUPASZ = r'(?:\(\d+[a-z]?\)(?:\s*[–-]\s*\(\d+[a-z]?\))?|[a-z]{1,2}\)(?:\s*[–-]\s*[a-z]{1,2}\))?)(?:\s+(?:\(\d+[a-z]?\)|[a-z]{1,2}\)))*'


def paragrafus_sorok(kod):
    if kod in _CACHE:
        return _CACHE[kod]
    p = kozos.korpusz_fajl(F[kod]['korpusz'][0])
    e = kozos.egyseg(kod)          # § vagy cikk, a beállításból; a fejsor szabálya: alapfelvetel.egyseg_sor
    d, cur = {}, None
    for l in open(p, encoding='utf-8').read().split('\n'):
        t = csillagtalan(l)
        m = kozos.egyseg_sor(t, e)
        if m:
            cur = m.group(1)
            if cur in d:
                cur = None; continue  # azonos számú második § (Itv.): az első számít
            d[cur] = []
            rest = t[m.end():].strip().lstrip('-–* ').strip()
            if rest and not (e != '§' and cimsor(rest)):
                d[cur].append(rest)       # a cikkfej utáni cím („3. cikk - Általános joghatóság”) nem normaszöveg
        elif cur is not None and t and t.isupper() and len(t) > 3 and not re.search(r'[.;:,]$', t):
            cur = None    # nagybetűs szerkezeti cím („ZÁRÓ ÉS VEGYES RENDELKEZÉSEK”, „II. FEJEZET”): az egység itt véget ér
        elif cur is not None and t:
            elozo = d[cur][-1] if d[cur] else ''
            if (re.fullmatch(r'\(\d+[a-z]?\)|[a-z]{1,2}\)', elozo) and not re.match(r'^(?:\(\d+[a-z]?\)|[a-z]{1,2}\) )', t)
                    and (l[:1].isspace() or t[:1].islower() or re.search(r'[.;:,]$', t))):
                # a PDF-ből vett korpuszban a bekezdés- vagy pontjel külön sorban áll („(1)” / „ Az európai …”): a jel és
                # a szöveg egy sor. A hatályon kívül helyezett puszta „(3)” után a következő jel vagy cím áll: az marad.
                d[cur][-1] = elozo + ' ' + t
                continue
            d[cur].append(t)
    _CACHE[kod] = d
    return d


def csoportok(sorok):
    """[(kulcs, [sorok])] a korpusz sorrendjében; címsorok és üres hatályon kívüli egységek nélkül."""
    out, cur = [], None
    sorok = kozos.zaro_cimek_le(sorok, cimsor)  # a következő § előtti szerkezeti címek (a folytatósor marad: KE-3/2)
    for l in sorok:
        if re.fullmatch(CSUPASZ, l):
            m = re.match(r'^\((\d+[a-z]?)\)', l)
            if m:
                cur = None; out.append(('hk' + m.group(1), [l]))  # hatályon kívül helyezett bekezdés
            elif out:
                out[-1][1].append(l)  # hatályon kívül helyezett pont
            continue
        if l.startswith('[') and l.endswith(']') and not out:
            out.append(('cim', [l])); continue
        m = re.match(r'^\((\d+[a-z]?)\) ', l)
        if m:
            cur = m.group(1); out.append((cur, [l])); continue
        if cur is None and (not out or out[-1][0] == 'cim'):
            cur = ''; out.append(('', [l])); continue
        if cur is None:
            continue
        out[-1][1].append(l)
    return out


def kulcs_keres(sor, cs):
    n = kozos.norm(re.sub(r'\((?:\.\.\.)\)|\[\.\.\.\]|…', ' ', sor))
    if sor.startswith('[') and sor.endswith(']'):
        return 'cim'
    m = re.match(r'^\((\d+[a-z]?)\) ', sor)
    if m and any(k == m.group(1) for k, _ in cs):
        return m.group(1)
    elso = n.split('  ')[0][:60]
    for k, ls in cs:
        if elso and elso in kozos.norm(' '.join(ls)):
            return k
    best = max(cs, key=lambda kv: difflib.SequenceMatcher(None, kozos.norm(' '.join(kv[1])), n, autojunk=False).ratio())
    return best[0]


def elemez(fej, sorok, utana=()):
    """A kozos.dobozok() mit olvasna ki a fejléc alá írt sorokból (a doboz utáni szöveggel együtt): ezzel ellenőrizzük,
    hogy a beírt doboz visszaolvasva ugyanaz-e (idempotencia)."""
    txt = '\n'.join([fej, ''] + [x for s in sorok for x in (s, '')] + [x for s in utana for x in (s, '')])
    d = kozos.dobozok(txt)
    return d[0][3] if d else []


def tordel(fej, jeloltek, minta=()):
    """A korpusz sorait dobozsorokká tördeli: a sor, amelyet a dobozfelismerő (kozos.dobozok) nem fogadna el önálló
    dobozsorként (a PDF-ből tördelt korpusz folytatósora, a pont után a bekezdés lezáró mondata stb.), az előző sorhoz
    csatlakozik. Így a beírt doboz visszaolvasva pontosan a beírt sorokat adja, és a második futás nem talál eltérést."""
    res = []
    mintak = [kozos.norm(m) for m in minta]
    for i, x in enumerate(jeloltek):
        if not res:
            res.append(x); continue
        egy = kozos.norm(res[-1] + ' ' + x)
        jeles = re.match(r'^(?:\(\d+[a-z]?\)(?: (?![a-záéíóöőúüű])|$)|[a-z]{1,2}\)(?: |$)|\d{1,3}(?:\.\d{1,2})*\. |[–-] '
                         r'|(?:i|ii|iii|iv|v|vi|vii|viii|ix|x)\. |\[)', x)
        if not jeles and any(egy in m for m in mintak):
            res[-1] = res[-1] + ' ' + x   # a tétel ezt a két korpuszsort egy sorban idézi: úgy marad
            continue
        lezart = re.search(r'[.;:!?…,\]]["”’)]*$', res[-1]) or re.fullmatch(r'\((?!\d+[a-z]?\))[^\n]*\)', res[-1])
        pontsor = re.match(r'^(?:[a-z]{1,2}\)|\d{1,3}(?:\.\d{1,2})*\.|[–-]|(?:i|ii|iii|iv|v|vi|vii|viii|ix|x)\.) ', res[-1])
        # a pont utáni kisbetűs sor a felsorolás lezáró szövege is lehet („e) az eljárás felfüggesztésének” / „nincs
        # helye.”): ott a dobozfelismerő dönt; a bekezdés- és bevezető sor folytatása egy sor marad
        kov = jeloltek[i + 1] if i + 1 < len(jeloltek) else ''
        pont_folyt = (pontsor and re.match(r'^[a-záéíóöőúüű]', x) and not jeles
                      and (re.search(r'[,;]$', x) or re.match(r'^(?:[a-z]{1,2}\)|[–-]) ', kov)))
        # a pont tördelt folytatása (a felsorolás közepén: utána újabb pont jön, vagy maga is „,”/„;”-vel zárul) – nem a
        # felsorolást lezáró szöveg
        vesszo = (not pontsor and re.search(r',["”’)]*$', res[-1]) and re.match(r'^[a-záéíóöőúüű]', x) and not jeles)
        # a vesszővel végződő bekezdés- vagy bevezető sor után kisbetűvel folytatódó sor: tördelt mondat
        if vesszo or not lezart and (pont_folyt or re.match(r'^\(\d+[a-z]?\) [a-záéíóöőúüű]', x)
                                     or not pontsor and not re.match(r'^(?:\(\d+[a-z]?\)|[a-z]{1,2}\) )', x)):
            res[-1] = res[-1] + ' ' + x   # a mondat a következő sorban folytatódik (tördelt korpusz): egy sor marad
            continue
        p = elemez(fej, res + [x] + jeloltek[i + 1:i + 2])
        if p[:len(res) + 1] == res + [x]:
            res.append(x)
        else:
            res[-1] = res[-1] + ' ' + x
    return res


def epit(fej, cs, kell, minta=()):
    """A doboz sorai a korpuszból: a kért bekezdések (kell: a csoportok() kulcsai) a korpusz sorrendjében, a köztük álló
    hatályon kívül helyezett bekezdésekkel, a dobozfelismerő szabálya szerint tördelve (tordel). EGYETLEN dobozépítő
    (KE-3/5): a doboz_javit újraépítése, az s5/alkalmaz.py @DOBOZ eleme és az s5/doboz_beszur.py is ezt használja.
    Vissza: (sorok, a ténylegesen felvett kulcsok halmaza)."""
    kell = set(kell)
    sor_k = [k for k, _ in cs]
    hely = [i for i, k in enumerate(sor_k) if k in kell and k != 'cim']
    if hely:
        kell |= {k for i, k in enumerate(sor_k) if k.startswith('hk') and hely[0] < i < hely[-1]}
    uj = [l for k, ls in cs if k in kell for l in ls]
    uj2 = []
    for i, x in enumerate(uj):
        if i and x.startswith('[') and uj2 and not uj2[-1].startswith('['):
            uj2[-1] += ' ' + x  # a felsorolást lezáró, szögletes zárójellel kezdődő szöveg a pont sorában marad
        else:
            uj2.append(x)
    return tordel(fej, uj2, minta), kell


_JOG = None


def doboz_epit(fej):
    """„Pp. 427. § (1)-(2)”, „EUMSZ 288. cikk” (dobozfejléc) -> ([fejléc] + a doboz sorai a korpuszból, None), vagy
    (None, ok). A bekezdés nélküli fejléc a teljes egységet (a szögletes cím nélkül) kéri."""
    global _JOG
    fej = fej.strip()
    m = kozos.doboz_fej(fej)
    if not m:
        return None, 'a fejléc nem értelmezhető (vagy az egysége nem a forrásé): ' + fej
    kod, par = kozos.fejlec_kod(m)
    if par == kozos.PREAMBULUM:
        return None, 'preambulumbekezdés doboza a korpuszból nem építhető (a bekezdéshatár nem állapítható meg): ' + fej
    if _JOG is None:
        _JOG = kozos.korpusz_jogszabalyok()
    if kod not in _JOG or kod not in F or par not in paragrafus_sorok(kod):
        return None, 'nincs ilyen %s a korpuszban: %s' % ('§' if kozos.egyseg(kod) == '§' else 'cikk', fej)
    cs = csoportok(paragrafus_sorok(kod)[par])
    maradek = fej[m.end(3):]
    kert = set()
    for a, b in re.findall(r'\((\d+[a-z]?)\)(?:\s*[–-]\s*\((\d+[a-z]?)\))?', maradek):
        if b:
            kulcsok = [k for k, _ in cs if not k.startswith('hk') and k != 'cim']
            if a in kulcsok and b in kulcsok and kulcsok.index(a) <= kulcsok.index(b):
                kert.update(kulcsok[kulcsok.index(a):kulcsok.index(b) + 1])
            else:
                return None, 'nincs ilyen bekezdés: ' + fej
        else:
            kert.add(a)
    if kert:
        hianyzik = [k for k in kert if k not in [x for x, _ in cs]]
        if hianyzik:
            return None, 'nincs ilyen bekezdés: %s (%s)' % (fej, ', '.join(hianyzik))
    else:
        kert = {k for k, _ in cs if k != 'cim'}
    sorok, _ = epit(fej, cs, kert)
    if not sorok:
        return None, 'üres doboz: ' + fej
    return [fej] + sorok, None


def folytatas(L, j, par_szov, par_sorok):
    """A doboz utáni sorok (j-től), amelyek a korpusz szerint ugyanannak a §-nak (cikknek) a szövegét folytatják (a
    dobozfelismerő a tördelt szöveg folytatósoránál lezárta a dobozt): [(index, sor)]. Csak a § szövegében betűre
    (normalizálva) meglévő sor számít; a rövid (15 karakternél rövidebb) sor csak akkor, ha a korpusz egy teljes sora."""
    out = []
    egesz = {kozos.norm(x) for x in par_sorok}
    while j < len(L):
        s = L[j].strip()
        if not s:
            j += 1; continue
        if kozos.doboz_fej(s) or s.isupper():
            break
        n = kozos.norm(re.sub(r'^\[[^\]]*\]\s*', '', s))
        if not n or n not in par_szov or (len(n) < 15 and n not in egesz):
            break
        out.append((j, s)); j += 1
    return out


def main():
    JOG = kozos.korpusz_jogszabalyok()
    TS = kozos.tetelsor()
    osszes, kihagyott = 0, 0
    for t in TS['tetelek']:
        n = t['sorszam']
        if TETELEK and n not in TETELEK:
            continue
        ut = os.path.join(kozos.GYOKER, f'{n:02d}.txt')
        txt = open(ut, encoding='utf-8').read()
        L = txt.split('\n')
        H = [i for i, l in enumerate(L) if kozos.doboz_fej(l)]
        cserek = []
        for (kod, par, fej, sorok), h in zip(kozos.dobozok(txt), H):
            if kod not in JOG or par not in paragrafus_sorok(kod) or not sorok or re.search(r'\)\s*pont$', fej):
                continue      # a pontot idéző doboz („Szabs. tv. 27. § (2) bek. a) pont”) szándékosan részleges
            ps = paragrafus_sorok(kod)[par]
            cs = csoportok(ps)
            if not cs:
                continue
            # a doboz sorai a fájlban: a fejléc után az első és az utolsó dobozsor
            idx, j = [], h + 1
            for s in sorok:
                while j < len(L) and L[j].strip() != s and not L[j].strip().endswith(s):
                    j += 1
                if j >= len(L):
                    break
                idx.append(j); j += 1
            if len(idx) != len(sorok):
                print(f'  !! {n}. {fej}: a dobozsorok nem találhatók'); kihagyott += 1; continue
            # a doboz után a § (cikk) szövegét folytató sorok (tördelt korpusz): a doboz részei
            tovabb = folytatas(L, idx[-1] + 1, kozos.norm(' '.join(ps)), ps)
            if tovabb:
                idx += [i for i, _ in tovabb]
                sorok = sorok + [x for _, x in tovabb]
            kell, elozo_k = set(), None
            for s in sorok:
                mc = re.match(r'^(\[[^\]]*\])\s+(\S.*)$', s)
                if mc:
                    kell.add('cim'); s = mc.group(2)
                # a bekezdésjel nélküli sor (a felsorolás lezáró szövege, tördelt folytatás) annak a bekezdésnek a része,
                # amelyben az előző sor áll, ha ott megvan („terjedő szabadságvesztéssel büntetendő.” több bekezdés végén is)
                ns = kozos.norm(re.sub(r'\((?:\.\.\.)\)|\[\.\.\.\]|…', ' ', s))
                ck = dict(cs)
                if (elozo_k is not None and not re.match(r'^\(\d+[a-z]?\) ', s) and elozo_k in ck
                        and ns.split('  ')[0][:60] in kozos.norm(' '.join(ck[elozo_k]))):
                    k = elozo_k
                else:
                    k = kulcs_keres(s, cs)
                kell.add(k); elozo_k = k
            egyutt = kozos.norm(re.sub(r'\((?:\.\.\.)\)|\[\.\.\.\]|…', ' ', ' '.join(sorok)))
            for k, ls in cs:
                # a bekezdés teljes első sora (legfeljebb 200 karakter) – az azonos kezdetű bekezdések („nyolc napon
                # belül” / „nyolc napon túl gyógyul”) ne keveredjenek
                probe = kozos.norm(re.sub(r'^\(\d+[a-z]?\)\s*|^\[[^\]]*\]\s*', '', ls[0]))[:200]
                if len(probe) >= 30 and probe in egyutt:
                    kell.add(k)
            if not any(x.startswith('[') for x in sorok):
                kell.discard('cim')
            uj, kell = epit(fej, cs, kell, sorok)
            if uj and sorok and not re.search(r'[.;:!?…]["”’)]*$', uj[-1]) and kozos.norm(sorok[-1]) in (
                    kozos.norm(uj[-1]) + '.', kozos.norm(uj[-1]) + ';'):
                uj[-1] += sorok[-1][-1]   # a korpuszból hiányzó záró írásjel (EUMSZ 10. cikk „… ellen”): a doboz írásjele marad
            hk = r'^\(?\d*[a-z]?\)?\s*Hatályon kívül helyezve\.?$|^[a-z]{1,2}\)\s*Hatályon kívül helyezve\.?$'
            tiszta = [s for s in sorok if not re.match(hk, s) and not re.fullmatch(CSUPASZ, s)]
            ujt = [s for s in uj if not re.fullmatch(CSUPASZ, s)]
            if [kozos.norm(x) for x in ujt] == [kozos.norm(x) for x in tiszta] or ('--sor' not in sys.argv and kozos.norm(' '.join(ujt)) == kozos.norm(' '.join(tiszta))):
                continue
            # visszaolvasás: a beírt doboz pontosan a beírt sorokat adja-e (a doboz utáni szöveggel együtt)
            utana = [x.strip() for x in L[idx[-1] + 1:] if x.strip()][:3]
            vissza = elemez(fej, uj, utana)
            if vissza != uj:
                kihagyott += 1
                tobb = len(vissza) > len(uj) and vissza[:len(uj)] == uj
                print(f'  !! {n}. {fej}: az újraépített doboz visszaolvasva eltér'
                      + (' (a doboz utáni szöveg is a dobozhoz kerülne)' if tobb else '') + ' – nem módosítva')
                continue
            if '--diff' in sys.argv:
                a = kozos.norm(' '.join(tiszta)).split(); b = kozos.norm(' '.join(ujt)).split()
                for o, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
                    if o != 'equal':
                        print('      ', o, '| tétel:', ' '.join(a[i1:i2])[:150], '| korpusz:', ' '.join(b[j1:j2])[:150])
            elotag = re.match(r'^(?:\d+(?::\d+)?(?:/[A-Z])?\. §|(?:\d+[a-z]?|[IVXLC]+)\. [Cc]ikk|[A-Z]\) [Cc]ikk)\s*', L[idx[0]].strip())
            uj_sorok = list(uj)
            if elotag:
                uj_sorok[0] = elotag.group(0) + uj_sorok[0]
            cserek.append((idx[0], idx[-1], uj_sorok))
            regi = sum(len(s) for s in sorok); ujh = sum(len(s) for s in uj)
            print(f'{n:>3}. {fej:<26} {sorted(kell, key=str)} {regi} -> {ujh} kar.' + (f' (+{len(tovabb)} folytatósor)' if tovabb else ''))
            osszes += 1
        if IR and cserek:
            for a, b, uj in sorted(cserek, reverse=True):
                blokk = []
                for k, s in enumerate(uj):
                    if k:
                        blokk.append('')
                    blokk.append(s)
                L[a:b + 1] = blokk
            open(ut, 'w', encoding='utf-8').write('\n'.join(L))
    if kihagyott:
        print('nem módosítható doboz:', kihagyott)
    print('módosítandó doboz:', osszes)


if __name__ == "__main__":
    main()
