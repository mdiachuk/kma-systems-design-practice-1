# How to run application

Requires Python 3.8.0

1. Install required dependencies:
```shell
pip install -r requirements.txt
```
2. Start the web server:
```shell
uwsgi --http 0.0.0.0:8000 --wsgi-file main.py --callable app --processes 4 --threads 2 --stats 127.0.0.1:9191
```