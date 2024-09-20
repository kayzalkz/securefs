git clone https://github.com/kayzalkz/securefs.git && cd securefs && openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365 && pip install requirements.txt && py app.py
