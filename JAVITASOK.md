# Elvégzett javítások - crypto_fibo_bot

Ez a dokumentum összefoglalja, mi változott, miért, és melyik fájlban keresd.
A logikát és a struktúrát nem írtam át - csak a konkrétan hibás/kockázatos
részeket javítottam, minimális beavatkozással.

---

## 🔴 1. SL/TP prioritás hiba (a legfontosabb javítás)
**Fájl:** `execution/trade_exit.py`

**Mi volt a hiba:** Ha egy gyertyán belül MIND a Stop Loss, MIND a Take Profit
szint teljesült, a bot mindig **WIN**-ként (nyereségként) könyvelte el, mert a
kód feltétel nélkül felülírta a korábban beállított "LOSS" eredményt.

**Mi lett a javítás:** Mostantól, ha mindkét szint teljesülne ugyanabban a
gyertyában, a bot konzervatívan a **SL-t (veszteség) részesíti előnyben** -
mert OHLC (nyitó/záró/max/min) adatból nem lehet biztosan megállapítani,
melyik szintet érte el előbb az ár a gyertyán belül. Ez a szokásos,
biztonságos gyakorlat backtesting/paper trading motoroknál.

A hozzá tartozó "PARTIAL TP" blokkot is összehangoltam, hogy ne könyveljen el
részleges profitot olyan esetben, amikor végül mégis a SL nyert prioritást.

**Teszteltem:** szimulált egy gyertyát, ami mindkét szintet érintette -
a régi logika +10 USD nyereséget mutatott volna, az új helyesen -5 USD
veszteséget könyvel el.

---

## 🟠 2. Egy hibázó symbol ne blokkolja/hagyja ki a többit
**Fájl:** `core/engine.py`

**Mi volt a hiba:** Ha 8 symbolt figyeltél, és a 3. symbolnál a Binance
lekérés hibázott (pl. időtúllépés), a teljes ciklus megszakadt - a 4-8.
symbol azon a körön egyáltalán nem lett megvizsgálva.

**Mi lett a javítás:** Minden symbol/timeframe candle-lekérése saját
try/except blokkba került. Ha egy adott symbol hibázik, azt kihagyjuk és a
ciklus folytatódik a többivel - nem áll meg az egész scan.

**Mellette:** `data/candles.py`-ban csökkentettem a retry várakozást
(2mp → 1mp), hogy egy hibázó hívás rövidebb ideig tartsa fel a többieket.

**Későbbi, nagyobb javítás (külön körben javasolt):** a bot jelenleg
szinkron, blokkoló REST hívásokkal kéri le a gyertyákat minden ciklusban.
Van egy `data/binance_ws.py` fájlod, ami websocket-alapú, valós idejű
adatlekérésre készült, de **jelenleg sehol nincs bekötve** a botba. Ennek
integrálása lenne a végleges megoldás a lassúságra/rate-limitre - ez nagyobb
átalakítás, javaslom külön menetben elvégezni.

---

## 🟡 3. State betöltés explicitté tétele + séma-migráció
**Fájlok:** `state.py`, `core/engine.py`, `main.py`

**Mi volt a hiba:** A `state.json` betöltése rejtetten, egy import
mellékhatásaként történt a `core/engine.py` tetején. Ez csak azért működött,
mert az importok sorrendje a `main.py`-ban véletlenül jó volt - bármilyen
átrendezés (pl. VS Code auto-import-rendezés) csendben elrontotta volna.

**Mi lett a javítás:** Új `initialize_state()` függvény a `state.py`-ban,
amit a `main.py` EXPLICIT módon, elsőként hív meg - jól látható, kereshető
helyen.

**Bónusz:** ugyanez a függvény automatikusan pótolja a `state.json`-ban
hiányzó mezőket minden symbolnál (pl. `price_precision` hiányzott
ETHUSDT-nél, BNBUSDT-nél, HFTUSDT-nél) a friss sablon alapján - így ha a
jövőben új mezőt vezetsz be a state szerkezetében, a régi mentések nem fognak
`KeyError`-ral elszállni.

---

## 🟡 4. Telegram token kiszervezése `.env`-be
**Fájlok:** `config.py`, `utils/env.py` (új), `.env` (új), `.env.example` (új)

A token korábban nyílt szövegben volt a `config.py`-ban. Mostantól egy külön
`.env` fájlból töltődik be (`utils/env.py` - saját, függőségmentes betöltő,
nem igényel extra pip csomagot). A `.gitignore` már korábban is kizárta a
`.env`-et, szóval ez biztonságos.

**⚠️ TEENDŐD:** A jelenlegi token megjelent ebben a beszélgetésben, ezért
javaslom, hogy a BotFathernél generálj egy ÚJAT (`/revoke` vagy `/token`), és
azt írd be a helyi `.env` fájlodba.

Mivel a `config.py` már nem tartalmaz titkot, akár git alá is vehetnéd
mostantól (jelenleg a `.gitignore` még kizárja) - ez a te döntésed, nem
kötelező.

---

## ⚪ 5. Kód-kupac eltakarítása
- `telegram/commands.py`: a duplikáltan definiált `set_active_symbol()`
  függvény egyik példánya törölve (a teljesebb, symbol-létrehozó verzió
  maradt).
- `strategy/fibo.py`: a sehol nem használt `build_fibo_context()` függvény
  törölve - ez duplikálta a `strategy/zones.py` -> `get_zones()` logikáját,
  két hely helyett most csak egy tartja karban a zóna-számítást.
- `config.py`: duplikáltan szereplő `telegram_enabled` kulcs összevonva.

---

## Amit NEM változtattam
- A Fibonacci zóna-számítás logikája (`strategy/zones.py`) helyes volt,
  nem nyúltam hozzá.
- A gyertyaminta-felismerés (`strategy/patterns.py`) működik, de érdemes
  tudnod: a hammer/shooting star detektálás jelenleg elég megengedő
  (majdnem doji gyertyákat is elfogadhat) - ez stratégiai finomhangolás
  kérdése, nem hiba, szólj ha ezt is szigorítani szeretnéd.
- `data/binance_ws.py` - lásd külön, 8. pont: időközben ezt is
  bekötöttem, immár nem érintetlen.

---

## 🔴 6. TRADE EXIT ellenőrzés leállt Range Invalid után
**Fájl:** `core/engine.py`

**Mi volt a hiba:** a `if symbol_state["range_invalid"]: continue` sor
**korábban** futott le, mint a TRADE EXIT (`check_trade_exit()`) hívás. Emiatt
amint egy symbol range-je invaliddá vált, a nyitott pozíció TP/SL
ellenőrzése **teljesen leállt** - minden további körben kiugrott a `continue`,
mielőtt elérte volna az exit-check-et. Ez ütközött a bot saját filozófiájával
("Range Invalid nem zár trade-et - a meglévő pozíció tovább él TP-ig,
SL-ig"). A pozíció csak úgy tudott lezárni, ha a bot időközben újraindult
(a `recovery.py` ugyanis nincs a `range_invalid`-hoz kötve).

**Mi lett a javítás:** a TRADE EXIT ellenőrzés most a range_invalid check
ELÉ került, és attól teljesen függetlenül fut le minden körben, amíg van
nyitott pozíció - nem csak az adott körben, hanem AZUTÁN is, korlátlan
ideig, amíg TP-t vagy SL-t nem talál. Ez extension szintű TP-kre (fibo
1.272, 1.618 - a range-en TÚL vannak) és az SL-re is helyesen működik,
amik szinte sosem esnek egybe a range invalidálódás pillanatával - ezt
két külön szimulációval (TP extension és SL) is leteszteltem, több körön
át.

---

## 🟡 7. Spot / Futures symbol támogatás
**Fájlok:** `state.py`, `data/candles.py`, `telegram/commands.py`

**Mi volt a probléma:** a bot kizárólag a Binance Spot API-t
(`api.binance.com`) hívta minden symbolra. Ha egy symbol csak Binance
Futures-ön van jegyezve (pl. `GWEIUSDT`), vagy TradingView-stílusú `.P`
végződéssel adtad meg (`GWEIUSDT.P`), a lekérés `400 Bad Request`-tel
elszállt.

**Mi lett a megoldás:**
- Új `normalize_symbol_input()` függvény (`state.py`): felismeri a `.P`
  végződést, levágja, és a symbolt automatikusan "futures" piachoz rendeli.
  `.P` nélkül marad "spot" - ez a régi, megszokott viselkedés.
- `data/candles.py`: symbolonként a megfelelő végpontot hívja
  (`api.binance.com` spot-hoz, `fapi.binance.com` futures-hez).
- `/add GWEIUSDT.P` és `/symbol GWEIUSDT.P` automatikusan felismeri és
  beállítja a piacot.
- Új `/market spot` / `/market futures` parancs egy már létező symbol
  piactípusának manuális átállítására.
- A meglévő 7 symbolod (BTCUSDT, ETHUSDT, stb.) mind automatikusan "spot"
  piacot kapott a migráció során - ahogy eddig is működtek, nem változik
  semmi náluk, amíg nem szólsz `/market futures`-szel az ellenkezőjét.

---

## 🟢 8. Websocket adatréteg (a lassú, blokkoló REST polling végleges megoldása)
**Fájlok:** `data/binance_ws.py` (teljesen újraírva), `core/engine.py`,
`main.py`, `requirements.txt` (új)

**A probléma, amit ez megold:** a bot korábban minden symbolnál/timeframe-nél
külön, szinkron REST hívást indított a fő ciklusban - lassú, és egy lassan
válaszoló hívás feltartja a többit is.

**A megoldás:** a `data/binance_ws.py` mostantól egy teljes, több-symbolos,
több-timeframe-es, Spot ÉS Futures websocket kliens:
- Két külön websocket kapcsolat (Spot: `stream.binance.com`, Futures:
  `fstream.binance.com`), mindkettő saját háttérszálon.
- Dinamikusan feliratkozik minden `state["symbols"]`-ben szereplő
  symbol/timeframe kombinációra - ha `/add`-olsz egy újat vagy módosítod a
  `/tf`-et, egy felügyelő szál (5mp-enként ellenőriz) automatikusan
  fel-/leiratkozik, **nem kell újraindítani a botot**.
- Automatikus újracsatlakozás, ha megszakad a kapcsolat (növekvő
  várakozással: 2mp → 4mp → ... → max 60mp).
- **A `core/engine.py` HIBRID módon használja**: minden candle-lekérésnél
  ELŐSZÖR a websocket cache-t próbálja (gyors, nem blokkol); ha még nincs
  rá adat, vagy elavult (30mp-nél régebbi), **automatikusan visszaesik a
  meglévő REST hívásra**. Tehát ha a websocket bármiért nem működne
  élesben nálad, a bot NEM áll le - csak lassabban, a régi módon folytatja.

**⚠️ FONTOS - amit neked kell tenned:**
1. Telepítsd a websocket-client csomagot, ha még nincs meg:
   `pip install websocket-client --break-system-packages`
   (a `requirements.txt`-be is belekerült)
2. **Ezt a részt nem tudtam élesben leteszteltetni** - a fejlesztői
   sandbox-nak nincs kimenő hálózati hozzáférése. Az üzenet-feldolgozó
   logikát alaposan teszteltem szimulált Binance üzenetekkel (lezárt
   gyertya, élő gyertya, ismeretlen symbol, elavult adat esetei mind
   lefedve), és az API-hívásokat (SUBSCRIBE/UNSUBSCRIBE mechanizmus,
   végpont URL-ek) a hivatalos Binance dokumentáció alapján írtam meg -
   de az élő kapcsolódást, hosszabb távú stabilitást neked kell
   megfigyelned éles indítás után. Ha bármi furcsát látsz a konzol
   logban (pl. `⚠ WS hiba`, `WS lezárva`), küldd el, átnézem.
3. Mivel van REST fallback, javaslom, hogy először **paper módban**,
   figyeld meg egy darabig a konzol logot, mielőtt élesre kapcsolnál vele.

---

## Ellenőrzés
Minden fájlt lefuttattam szintaktikai ellenőrzésen (`py_compile`) és
import-teszten - mind hibamentes. Az SL/TP javítást szimulált teszttel is
ellenőriztem. A `state.json`-od érintetlen maradt.
