git clone https://github.com/kayzalkz/securefs.git && cd securefs && pip install -r requirements.txt && openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365 && py app.py
