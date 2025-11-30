release: python manage.py migrate && python manage.py init_render
web: exec gunicorn --bind 0.0.0.0:${PORT:-10000} --workers 2 --timeout 60 koki_foodhub.wsgi
