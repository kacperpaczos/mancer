# Basic Web Preset

Ten preset instaluje podstawowe środowisko webowe z następującymi komponentami:

## Zainstalowane komponenty
- Nginx (serwer webowy)
- Apache2 (alternatywny serwer webowy)
- Flask (framework Python)
- Gunicorn (serwer WSGI)

## Użycie
Po instalacji presetu:

1. Aplikacja Flask jest dostępna na porcie 5000
2. Nginx proxy jest skonfigurowany na porcie 80
3. Możesz modyfikować aplikację w `/var/www/flask_app/app.py`

## Zarządzanie usługami
```bash
# Sprawdź status aplikacji Flask
systemctl status flask_app

# Sprawdź status Nginx
systemctl status nginx

# Zrestartuj aplikację Flask
systemctl restart flask_app

# Zrestartuj Nginx
systemctl restart nginx
```

## Testowanie
Możesz przetestować działanie serwera wykonując:
```bash
curl http://localhost
# lub
curl http://localhost:5000
``` 