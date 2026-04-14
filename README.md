# CNAIR eRovinieta Gratuit

Integrare custom pentru Home Assistant care citește date din contul CNAIR eRovinieta.

## Funcții

Integrarea oferă senzori pentru:

- date utilizator
- rovinietă activă pentru fiecare vehicul
- data început / sfârșit rovinietă
- zile rămase până la expirare
- treceri pod
- restanțe treceri pod
- sold peaje neexpirate

## Cerințe

- Home Assistant
- cont valid pe platforma CNAIR eRovinieta

## Instalare prin HACS

### Custom repository

1. Deschide HACS
2. Mergi la **Integrations**
3. Apasă pe meniul cu 3 puncte
4. Alege **Custom repositories**
5. Adaugă repository-ul acestui proiect
6. Alege tipul **Integration**
7. Instalează integrarea
8. Repornește Home Assistant

## Instalare manuală

1. Copiază folderul `custom_components/erovinieta_free` în:
   `/config/custom_components/erovinieta_free`
2. Repornește Home Assistant
3. Adaugă integrarea din **Settings → Devices & Services**

## Configurare

La adăugarea integrării vei introduce:

- username
- password
- intervalul de actualizare

## Entități create

Pentru fiecare vehicul pot fi create entități de tip:

- `Rovinietă activă (...)`
- `Treceri pod (...)`
- `Restanțe treceri pod (...)`
- `Sold peaje neexpirate (...)`

În plus, este creat și senzorul:

- `Date utilizator`

## Observații

- Integrarea depinde de disponibilitatea și structura actuală a platformei CNAIR eRovinieta.
- Dacă CNAIR schimbă site-ul sau endpoint-urile folosite, integrarea poate necesita actualizare.
- Senzorul **Date utilizator** poate expune date personale sensibile în Home Assistant.

## Disclaimer

Acest proiect este independent și nu este afiliat oficial cu CNAIR.

## Licență

MIT License