# CodeLab — AI mentor pre výučbu programovania

Lokálne spustiteľný webový systém na vzdelávanie v programovaní s integrovaným AI mentorom v sokratovskom móde. Implementačný výstup diplomovej práce na FMFI UK Bratislava.

## Hlavné funkcie

- **Bezpečné spúšťanie kódu** v Docker sandboxe pre Python, C++ a Javu
- **AI mentor** v sokratovskom móde (lokálna Llama 3.1 8B cez Ollama) — model vedie študenta otázkami namiesto priameho riešenia
- **Štyri typy úloh** — písanie kódu, hľadanie chyby, písanie testov, refaktorizácia
- **Automatické vyhodnocovanie** odovzdaní s porovnaním proti referenčnej implementácii
- **Generátor úloh** poháňaný lokálnym LLM
- **Bočný panel hodnotenia** s klávesovými skratkami pre efektívnu prácu učiteľa
- **História spustení** každého študenta, hodnotenie 1–10 + komentár

## Architektúra

- **Backend:** Django 5.2 + PostgreSQL
- **Frontend:** Bootstrap 5 + Monaco Editor (vanilla JS, žiadny framework)
- **Sandbox:** Docker kontajner (Python 3.9-slim + g++ + default-jdk)
- **AI:** Ollama server s modelom Llama 3.1 8B, lokálne — bez závislosti na cloude
- **Dáta:** všetko zostáva na fakultnom hardvéri (GDPR-friendly)

## Inštalácia

### Predpoklady

- Python ≥ 3.9
- PostgreSQL (lokálne alebo cez Docker)
- Docker daemon (pre sandbox)
- [Ollama](https://ollama.com/) s modelom `llama3` (`ollama pull llama3`)

### Krok za krokom

```bash
# 1. Klonovanie repa
git clone https://github.com/SamuelJesik/DP.git
cd DP

# 2. Virtuálne prostredie
python -m venv venv
# Windows:
.\venv\Scripts\Activate.ps1
# Linux/macOS:
source venv/bin/activate

# 3. Závislosti
pip install -r requirements.txt

# 4. Databáza (PostgreSQL musí bežať a databáza "DP" existovať)
#    Predvolené prihl. údaje v settings.py: user=postgres, password=postgres
python manage.py migrate

# 5. Defaultný superužívateľ: admin / admin123
python manage.py loaddata initial_superuser

# 6. Build Docker sandbox image
docker build -t python-runner .

# 7. Spustenie Ollama (v samostatnom termináli)
ollama serve

# 8. Django dev server
python manage.py runserver
```

Aplikácia beží na <http://127.0.0.1:8000/myapp/>.

## Roly

- **Učiteľ (`is_superuser`)** — pridáva úlohy, generuje ich cez AI, hodnotí riešenia študentov cez bočný panel
- **Študent** — rieši úlohy, používa AI mentora, dostáva spätnú väzbu a hodnotenie

## Štruktúra projektu

```
manage.py              vstupný bod Django
DP/                    konfigurácia projektu (settings, urls, wsgi)
myapp/                 hlavná logika (models, views, urls, forms)
templates/             HTML šablóny
test_directory/        zdieľaný adresár medzi Django a Docker (run-time)
Dockerfile             definícia sandbox image
```

## Limity

- Aktuálne beží na Django dev serveri — produkčné nasadenie by vyžadovalo Gunicorn + Nginx
- Latencia AI mentora bez GPU je 10–40 sekúnd; s GPU klesá pod 3 sekundy
- Z taxonómie obranných mechanizmov je implementovaný iba **automatický test runner**; pokročilejšie moduly (behavior preservation checker, špecifikačný linter, multi-model verification) tvoria roadmap ďalšieho vývoja

## Licencia a kontext

Implementačný výstup diplomovej práce. Text práce, dotazníkové dáta a artefakty komparatívneho experimentu medzi LLM modelmi nie sú súčasťou tohto repozitára.

© 2025/2026 Bc. Samuel Ješík — Fakulta matematiky, fyziky a informatiky, Univerzita Komenského v Bratislave
