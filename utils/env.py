# utils/env.py
#
# Nagyon egyszerű, függőségmentes .env betöltő.
# Nem igényli a python-dotenv csomag telepítését -
# csak beolvassa a KEY=VALUE sorokat a .env fájlból,
# és beteszi őket os.environ-be (ha még nincsenek ott).

import os


def load_env(path=".env"):

    if not os.path.exists(path):
        return

    with open(path, "r", encoding="utf-8") as f:

        for line in f:

            line = line.strip()

            # üres sorok és kommentek kihagyása
            if not line or line.startswith("#"):
                continue

            if "=" not in line:
                continue

            key, _, value = line.partition("=")

            key = key.strip()
            value = value.strip()

            # idézőjelek levágása, ha vannak
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
                value = value[1:-1]

            # nem írjuk felül, ha már be van állítva
            # (pl. rendszerszintű env változó, szerveren)
            os.environ.setdefault(key, value)
