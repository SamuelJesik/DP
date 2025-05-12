# Diplomová práca: Využitie UI v procese výuky programovania

Diplomová práca **“Využitie UI v procese výučby programovania”** (Bc. Samuel Ješík, FMFI UK).

---

## Prehľad

Webová aplikácia umožňuje študentom:
- písanie a spúšťanie kódu (Python, C++, Java) v izolovanom Docker-sandboxe  
- generovanie a hodnotenie testov  
- refaktoring a analýzu AI-generovaného kódu  

---

## Požiadavky

- **Python** ≥ 3.9  
- **Docker** & **Docker Compose** (len pre sandbox spúšťanie kódu)  
- **PostgreSQL** + **pgAdmin** (lokálna inštalácia alebo cez Docker)  
- PowerShell (Windows) alebo Bash (Linux/macOS)  

---

## Rýchly štart

1. **Skopírujte repozitár a zmeňte pracovný adresár**  
  - cd C:\Users\<užívateľ>\Projects\DP
   
2. **Aktivujte virtuálne prostredie**

  - .\venv\Scripts\Activate.ps1   # Windows PowerShell

3. **Spustite server**
 - python manage.py runserver

4. **V prehliadači choďte na**
 - http://127.0.0.1:8000/myapp
