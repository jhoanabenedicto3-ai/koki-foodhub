release: python manage.py migrate && python manage.py init_render
web: exec gunicorn --bind 0.0.0.0:${PORT:-10000} koki_foodhub.wsgi
