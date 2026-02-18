# Rezervační Systém – Správce zasedaček

## Popis domény

Aplikace slouží ke **správě rezervací zasedacích místností** ve firmě. Uživatelé si mohou rezervovat místnosti na konkrétní čas, přičemž systém hlídá kapacitu, kolize, pracovní dny a limity rezervací na uživatele.

### Doménové entity

| Entita | Popis |
|---|---|
| **Room** | Zasedací místnost s názvem a kapacitou |
| **User** | Uživatel systému (jméno, e-mail) |
| **Booking** | Rezervace – propojuje uživatele s místností v daném čase |

### Vztahy

- **Room → Booking** (1:N) – místnost může mít mnoho rezervací
- **User → Booking** (1:N) – uživatel může mít více rezervací

### Business pravidla

1. **Validace vstupů** – název místnosti nesmí být prázdný, kapacita a počet účastníků musí být kladné
2. **Kontrola kapacity** – počet účastníků nesmí přesáhnout kapacitu místnosti
3. **Validace časů** – konec rezervace musí být po začátku
4. **Pracovní dny** – rezervace jsou povoleny pouze Po–Pá
5. **Limit rezervací** – uživatel smí mít max. 2 budoucí rezervace
6. **Kontrola kolizí** – místnost nesmí mít překrývající se rezervace

---

## Jak spustit projekt

### Prerekvizity
- Python 3.10+
- Git

### Instalace a spuštění lokálně

```bash
# 1. Klonování
git clone https://github.com/JanCermakW/spravce-zasedacek.git
cd spravce-zasedacek

# 2. Virtuální prostředí
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 3. Instalace závislostí
pip install -r requirements.txt

# 4. Spuštění serveru
uvicorn app.main:app --reload
```

- Aplikace: http://127.0.0.1:8000
- Swagger UI: http://127.0.0.1:8000/docs

---

## Testy

```bash
# Spuštění všech testů
pytest

# S coverage reportem
pytest --cov=app --cov-report=term-missing

# Generování HTML reportu
pytest --cov=app --cov-report=html
```

### Cíl pokrytí

- **Line coverage:** ≥ 80 %
- **Branch coverage:** ≥ 60 %

Co záměrně netestujeme: `database.py` (infrastrukturní kód – vytvoření engine a session generátor), `__init__.py` soubory.

---

## Architektura

```
Klient (HTTP)  →  main.py (Controller/API)  →  services.py (Business logika)  →  models.py (Entity/DB)
```

### Vrstvená architektura

| Vrstva | Soubor | Odpovědnost |
|---|---|---|
| **API (Controller)** | `app/main.py` | REST endpointy, HTTP kódy, dependency injection |
| **Service (Business)** | `app/services.py` | Veškerá doménová logika a validace – jádro TDD |
| **Model (Data)** | `app/models.py` | Definice entit (SQLModel), schéma DB |
| **Infrastruktura** | `app/database.py` | Připojení k SQLite, session management |

### Technologie

- **Jazyk:** Python 3.10
- **Framework:** FastAPI
- **ORM:** SQLModel (SQLAlchemy + Pydantic)
- **Databáze:** SQLite (produkce i vývoj), in-memory SQLite (testy)
- **CI/CD:** GitHub Actions

---

## Testovací strategie

### Unit testy (`tests/test_logic.py`)

Testují **izolovanou business logiku** ve třídě `BookingService`. Každé business pravidlo má testy na:
- **negativní scénář** (pravidlo porušeno → `ValueError`)
- **pozitivní scénář** (validní vstup → `True`)
- **hraniční stavy** (např. kapacita == attendees, end == start, navazující rezervace)

### Integrační testy (`tests/test_api.py`)

Testují **celou cestu** HTTP request → Controller → Service → databáze (in-memory SQLite). Ověřují:
- správné HTTP status kódy (200, 400, 404)
- obsah chybových zpráv v JSON response
- end-to-end flow (vytvoření místnosti, uživatele, rezervace)

### Mocking

V unit testech používáme `unittest.mock.Mock` jako náhradu za databázovou **Session**. Důvod: unit testy business logiky mají být **rychlé a izolované** od databáze. Mockujeme:
- `session.exec().first()` – pro `check_availability` (simulace existující/neexistující rezervace)
- `session.exec().one()` – pro `validate_user_limit` (simulace počtu rezervací)

V integračních testech naopak mockování **nepoužíváme** – pracujeme s reálnou in-memory SQLite databází přes `StaticPool`, abychom ověřili integraci všech vrstev.

### Struktura testů (AAA)

Všechny testy dodržují vzor **Arrange–Act–Assert**:
1. **Arrange** – příprava dat (vytvoření Room, User, Mock)
2. **Act** – volání testované metody / HTTP requestu
3. **Assert** – ověření výsledku (`pytest.raises`, status kód, JSON body)