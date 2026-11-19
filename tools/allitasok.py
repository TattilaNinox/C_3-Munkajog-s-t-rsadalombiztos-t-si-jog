#!/usr/bin/env python3
"""A tétel magyarázó bekezdései közül azok, amelyek határidőt, számot, feltételt, kivételt, semmisséget állítanak (ellenőrzési segédlet).
Használat: allitasok.py <tétel> [max_karakter]"""
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kozos
n = int(sys.argv[1]); mx = int(sys.argv[2]) if len(sys.argv) > 2 else 420
kulcs = re.compile(r'\b(\d+|egy|két|három|négy|öt|hat|hét|nyolc|tíz|tizenöt|harminc|hatvan|kilencven)\s*(napos|nap|éves|év|hónapos|hónap|százalék)|semmis|jogvesztő|elévül|kivéve|csak akkor|kizárólag|legfeljebb|legalább|szakirodalom|bírói gyakorlat|joggyakorlat szerint', re.I)
for b in kozos.tetel_szoveg(n).split('\n\n'):
    b = b.strip()
    if len(b) < 150 or re.match(r'^\(?\d*[a-z]?\)', b) or '\n(' in b: continue
    m = kulcs.search(b)
    if m:
        i = max(0, m.start() - mx // 2)
        print('•', ('…' if i else '') + b[i:i + mx].replace('\n', ' '))
