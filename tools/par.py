#!/usr/bin/env python3
"""Egy § normalizált szövege a korpuszból:  python3 tools/par.py Ptk 5:44 [5:45 …]"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kozos
J = kozos.korpusz_jogszabalyok()
for p in sys.argv[2:]:
    print(f'--- {sys.argv[1]} {p}. §'); print(J[sys.argv[1]][0].get(p, 'NINCS'))
