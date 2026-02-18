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

## Architektura systému

### Diagram architektury

```
┌─────────────────────────────────────────────────────────────────────┐
│                        GitHub Actions CI/CD                        │
│  ┌─────────┐  ┌────────────┐  ┌───────────────┐  ┌─────────────┐  │
│  │  Lint   │→│ Unit Tests │→│ Integ. Tests  │→│ Build Image │  │
│  │ (flake8)│  │  (pytest)  │  │(pytest + PG)  │  │  (GHCR)     │  │
│  └─────────┘  └────────────┘  └───────────────┘  └──────┬──────┘  │
│                                                          │         │
│                                              ┌───────────▼───────┐ │
│                                              │  Deploy Staging   │ │
│                                              │ (kubectl apply)   │ │
│                                              └───────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────── Kubernetes Cluster ──────────────────┐
│                                                                     │
│  ┌──────────── Namespace: staging ────────────┐                     │
│  │  ┌──────────────┐     ┌─────────────────┐  │                     │
│  │  │ stg-app (1x) │────▶│ stg-postgres    │  │                     │
│  │  │  Port 8000   │     │  Port 5432      │  │                     │
│  │  └──────┬───────┘     └─────────────────┘  │                     │
│  │         │                                   │                     │
│  │  ┌──────▼───────┐                           │                     │
│  │  │ Ingress      │                           │                     │
│  │  │ staging.local│                           │                     │
│  │  └──────────────┘                           │                     │
│  └─────────────────────────────────────────────┘                     │
│                                                                     │
│  ┌──────────── Namespace: production ─────────┐                     │
│  │  ┌──────────────┐     ┌─────────────────┐  │                     │
│  │  │prod-app (2x) │────▶│ prod-postgres   │  │                     │
│  │  │  Port 8000   │     │  Port 5432      │  │                     │
│  │  └──────┬───────┘     └─────────────────┘  │                     │
│  │         │                                   │                     │
│  │  ┌──────▼───────┐                           │                     │
│  │  │ Ingress      │                           │                     │
│  │  │ app.local    │                           │                     │
│  │  └──────────────┘                           │                     │
│  └─────────────────────────────────────────────┘                     │
└─────────────────────────────────────────────────────────────────────┘

┌───── Datový tok ─────┐
│                       │
│  Klient (HTTP)        │
│       │               │
│       ▼               │
│  Ingress (nginx)      │
│       │               │
│       ▼               │
│  FastAPI (main.py)    │
│       │               │
│       ▼               │
│  Service (services.py)│
│       │               │
│       ▼               │
│  SQLModel (models.py) │
│       │               │
│       ▼               │
│  PostgreSQL           │
└───────────────────────┘
```

### Vrstvená architektura aplikace

| Vrstva | Soubor | Odpovědnost |
|---|---|---|
| **API (Controller)** | `app/main.py` | REST endpointy, HTTP kódy, dependency injection |
| **Service (Business)** | `app/services.py` | Veškerá doménová logika a validace – jádro TDD |
| **Model (Data)** | `app/models.py` | Definice entit (SQLModel), schéma DB + Create schémata |
| **Infrastruktura** | `app/database.py` | Připojení k PostgreSQL/SQLite, session management |

### Technologie

- **Jazyk:** Python 3.10
- **Framework:** FastAPI
- **ORM:** SQLModel (SQLAlchemy + Pydantic)
- **Databáze:** PostgreSQL 16 (produkce/staging), SQLite (lokální vývoj fallback)
- **Kontejnerizace:** Docker (multi-stage build)
- **Orchestrace:** Kubernetes + Kustomize
- **CI/CD:** GitHub Actions → GHCR (GitHub Container Registry)
- **Linting:** flake8

---

## Jak spustit projekt

### Varianta 1 – Lokálně (Python)

**Prerekvizity:** Python 3.10+, Git

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

# 4. Spuštění serveru (SQLite jako výchozí DB)
uvicorn app.main:app --reload
```

- Aplikace: http://127.0.0.1:8000
- Swagger UI: http://127.0.0.1:8000/docs

### Varianta 2 – Docker Compose (doporučeno)

**Prerekvizity:** Docker, Docker Compose

```bash
# Spuštění aplikace + PostgreSQL
docker-compose up --build

# Spuštění na pozadí
docker-compose up --build -d

# Zastavení
docker-compose down

# Zastavení + smazání dat
docker-compose down -v
```

Aplikace běží na http://localhost:8000, PostgreSQL na portu 5432.

### Varianta 3 – Pouze Docker (bez compose)

```bash
# Build image
docker build -t spravce-zasedacek:latest .

# Spuštění (vyžaduje externí PostgreSQL)
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@host:5432/dbname \
  spravce-zasedacek:latest
```

---

## Databáze

Aplikace podporuje dvě databáze přes proměnnou prostředí `DATABASE_URL`:

| Prostředí | Databáze | Konfigurace |
|---|---|---|
| **Lokální vývoj** | SQLite | Výchozí – žádná konfigurace potřeba |
| **Docker Compose** | PostgreSQL 16 | Automaticky nastaveno v `docker-compose.yml` |
| **Kubernetes** | PostgreSQL 16 | ConfigMap + Secret |
| **CI (integrační testy)** | PostgreSQL 16 | GitHub Actions service container |

```bash
# Příklad: přepnutí na PostgreSQL lokálně
export DATABASE_URL=postgresql://user:password@localhost:5432/zasedacky
uvicorn app.main:app --reload
```

---

## Testy

```bash
# Spuštění všech testů
pytest

# S coverage reportem
pytest --cov=app --cov-report=term-missing

# Generování HTML reportu
pytest --cov=app --cov-report=html

# Lint kontrola
flake8 app/ --max-line-length=120
```

### Cíl pokrytí

- **Line coverage:** ≥ 80 %
- **Branch coverage:** ≥ 60 %

Co záměrně netestujeme: `database.py` (infrastrukturní kód – vytvoření engine a session generátor), `__init__.py` soubory.

---

## CI/CD Pipeline

Pipeline je definován v `.github/workflows/pipeline.yml` a spouští se při **push** a **pull request** do větve `main`.

### Kroky pipeline

```
push/PR → Lint → Unit Tests → Integration Tests → Build Image → Deploy Staging
                                    (PostgreSQL)       (GHCR)     (kubectl)
```

| Job | Popis | Detaily |
|---|---|---|
| **lint** | Statická analýza kódu | `flake8` s max-line-length=120 |
| **unit-tests** | Unit testy business logiky | `pytest` s coverage reportem, upload HTML artefaktu |
| **integration-tests** | Integrační testy s reálnou DB | PostgreSQL 16 service container, testy přes HTTP |
| **build-image** | Sestavení a push Docker image | Multi-stage build, push do `ghcr.io` |
| **deploy-staging** | Nasazení do staging prostředí | `kubectl apply -k k8s/overlays/staging` |

### Artefakty

- **HTML Coverage Report** – stažitelný z GitHub Actions po dokončení `unit-tests` jobu

---

## Kubernetes nasazení

Manifesty jsou organizovány pomocí **Kustomize** ve složce `k8s/`:

```
k8s/
├── base/                        # Společné manifesty
│   ├── kustomization.yaml
│   ├── namespace.yaml
│   ├── postgres-secret.yaml     # DB credentials (base64)
│   ├── postgres-configmap.yaml
│   ├── postgres-deployment.yaml
│   ├── postgres-service.yaml
│   ├── app-configmap.yaml       # DATABASE_URL
│   ├── app-deployment.yaml      # Readiness + liveness probes
│   ├── app-service.yaml
│   └── app-ingress.yaml         # Nginx Ingress
├── overlays/
│   ├── staging/                 # Staging prostředí
│   │   ├── kustomization.yaml   # namePrefix: stg-, replicas: 1
│   │   └── patches/
│   └── production/              # Produkční prostředí
│       ├── kustomization.yaml   # namePrefix: prod-, replicas: 2
│       └── patches/
```

### Nasazení do staging

```bash
# Prerekvizity: kubectl, minikube/kind
minikube start
minikube addons enable ingress

# Nasazení staging prostředí
kubectl apply -k k8s/overlays/staging

# Ověření
kubectl get pods -n staging
kubectl get svc -n staging

# Port-forward pro přístup k aplikaci
kubectl port-forward -n staging svc/stg-app 8000:80
# → http://localhost:8000/docs
```

### Nasazení do produkce

```bash
# Nasazení produkčního prostředí
kubectl apply -k k8s/overlays/production

# Ověření
kubectl get pods -n production
kubectl get svc -n production

# Port-forward
kubectl port-forward -n production svc/prod-app 8000:80
```

### Rozdíly mezi prostředími

| Vlastnost | Staging | Produkce |
|---|---|---|
| **Namespace** | `staging` | `production` |
| **Name prefix** | `stg-` | `prod-` |
| **Repliky aplikace** | 1 | 2 |
| **DB heslo** | `staging_password` | Nastaveno přes CI/CD secret |
| **Ingress host** | `staging.local` | `app.local` |

---

## Docker

### Dockerfile – multi-stage build

```
Stage 1 (builder):   python:3.10-slim → instalace závislostí
Stage 2 (runtime):   python:3.10-slim → kopie závislostí + kódu
```

**Bezpečnostní opatření:**
- Non-root uživatel (`appuser`)
- Healthcheck (`/docs` endpoint, interval 30s)
- Minimální base image (`slim`)
- `.dockerignore` vylučuje `__pycache__`, `venv`, `.pytest_cache`, `.env`

---

## Správa tajemství (Secrets)

| Co | Kde | Jak |
|---|---|---|
| **DB heslo (staging)** | `k8s/overlays/staging/patches/postgres-secret.yaml` | Base64 encoded v YAML |
| **DB heslo (produkce)** | CI/CD pipeline | GitHub Secrets → `kubectl create secret` |
| **GHCR token** | GitHub Actions | Automatický `GITHUB_TOKEN` |
| **DATABASE_URL** | ConfigMap (`app-configmap.yaml`) | Per-environment overlay patch |

Produkční hesla **nikdy** nejsou uložena v repozitáři. V CI/CD pipeline se používají GitHub Secrets, které se injektují při nasazení.

---

## Git workflow

- **Hlavní větev:** `main`
- **Feature větve:** `feature/*` – pro nové funkce a úpravy
- **Commit konvence:** popisné commit zprávy v češtině/angličtině
- **Pull requesty:** CI pipeline se spustí automaticky, merge po úspěšném průchodu

---

## Testovací strategie

### Unit testy (`tests/test_logic.py`)

Testují **izolovanou business logiku** ve třídě `BookingService`. Každé business pravidlo má testy na:
- **negativní scénář** (pravidlo porušeno → `ValueError`)
- **pozitivní scénář** (validní vstup → `True`)
- **hraniční stavy** (např. kapacita == attendees, end == start, navazující rezervace)

### Integrační testy (`tests/test_api.py`)

Testují **celou cestu** HTTP request → Controller → Service → databáze (in-memory SQLite). Ověřují:
- správné HTTP status kódy (200, 400, 404, 409)
- obsah chybových zpráv v JSON response
- end-to-end flow (vytvoření místnosti, uživatele, rezervace)
- duplikátní záznamy (e-mail uživatele)

V CI pipeline integrační testy běží proti **reálnému PostgreSQL** service containeru.

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