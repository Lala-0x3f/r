from flask import request
from geoip2.database import Reader

r = Reader('api/geoip/Country.mmdb')

def get_user_ip():
    user_ip = request.remote_addr
    try:
        c = r.country(user_ip).country.name
    except Exception:
        c = f'No Geoip data match user ip {str(Exception)}'
    return f"🧭Request from ip:[{user_ip}] --> {c} "

print(type(r))