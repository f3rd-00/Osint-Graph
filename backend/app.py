import math
import os
import re
from io import BytesIO
from pathlib import Path

from flask import Flask, jsonify, send_from_directory
from PIL import Image, ImageDraw
import requests

BASE_DIR = Path(__file__).resolve().parent
IMAGES_DIR = BASE_DIR / "images"
IMAGES_DIR.mkdir(exist_ok=True)

app = Flask(__name__)


@app.after_request
def add_cors_headers(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return resp


def _latlon_to_pixel(lat, lon, zoom):
    n = 256 * (2 ** zoom)
    x = (lon + 180.0) / 360.0 * n
    lat_rad = math.radians(lat)
    y = (1.0 - math.log(math.tan(lat_rad) + 1 / math.cos(lat_rad)) / math.pi) / 2.0 * n
    return x, y


def save_static_map(lat, lon, filename, zoom=17, size=420):
    lat = float(lat)
    lon = float(lon)
    center_x, center_y = _latlon_to_pixel(lat, lon, zoom)
    half = size / 2
    left, top = center_x - half, center_y - half
    right, bottom = center_x + half, center_y + half

    tile_x_min, tile_x_max = int(left // 256), int(right // 256)
    tile_y_min, tile_y_max = int(top // 256), int(bottom // 256)

    canvas = Image.new("RGB", ((tile_x_max - tile_x_min + 1) * 256, (tile_y_max - tile_y_min + 1) * 256), (230, 230, 230))
    headers = {"User-Agent": "outrasec-tool/1.0 (uso pessoal, nao automatizado em massa)"}
    n_tiles = 2 ** zoom

    for tx in range(tile_x_min, tile_x_max + 1):
        for ty in range(tile_y_min, tile_y_max + 1):
            tx_wrapped = tx % n_tiles
            url = f"https://tile.openstreetmap.org/{zoom}/{tx_wrapped}/{ty}.png"
            try:
                r = requests.get(url, headers=headers, timeout=10)
                r.raise_for_status()
                tile_img = Image.open(BytesIO(r.content)).convert("RGB")
            except Exception:
                tile_img = Image.new("RGB", (256, 256), (220, 220, 220))
            canvas.paste(tile_img, ((tx - tile_x_min) * 256, (ty - tile_y_min) * 256))

    crop_left = int(left - tile_x_min * 256)
    crop_top = int(top - tile_y_min * 256)
    cropped = canvas.crop((crop_left, crop_top, crop_left + size, crop_top + size))

    draw = ImageDraw.Draw(cropped)
    cx, cy, r = size // 2, size // 2, 7
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(220, 30, 30), outline=(255, 255, 255), width=2)

    path = IMAGES_DIR / filename
    cropped.save(path, "PNG")
    return f"/images/{filename}"


@app.route("/api/health")
def health():
    return jsonify({"ok": True, "msg": "backend rodando"})


@app.route("/images/<path:filename>")
def serve_image(filename):
    return send_from_directory(IMAGES_DIR, filename)


@app.route("/api/cep/<cep>")
def lookup_cep(cep):
    cep_digits = re.sub(r"\D", "", cep)
    if len(cep_digits) != 8:
        return jsonify({"ok": False, "error": "CEP inválido, use 8 dígitos (ex: 01310930)"}), 400

    try:
        r = requests.get(f"https://viacep.com.br/ws/{cep_digits}/json/", timeout=10)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        return jsonify({"ok": False, "error": f"Falha ao consultar ViaCEP: {e}"}), 502

    if data.get("erro"):
        return jsonify({"ok": False, "error": "CEP não encontrado"}), 404

    address = f"{data.get('logradouro','')}, {data.get('bairro','')}, {data.get('localidade','')} - {data.get('uf','')}"

    try:
        geo = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": address, "format": "json", "limit": 1},
            headers={"User-Agent": "outrasec-tool/1.0 (uso pessoal)"},
            timeout=15,
        )
        geo.raise_for_status()
        results = geo.json()
    except Exception as e:
        return jsonify({"ok": False, "error": f"Falha ao geocodificar o endereço: {e}", "endereco": address}), 502

    if not results:
        return jsonify({"ok": False, "error": "Endereço não localizado no mapa", "endereco": address}), 404

    lat = results[0]["lat"]
    lon = results[0]["lon"]

    filename = f"cep_{cep_digits}.png"
    try:
        image_url = save_static_map(lat, lon, filename)
    except Exception:
        image_url = None

    return jsonify({
        "ok": True,
        "cep": cep_digits,
        "logradouro": data.get("logradouro"),
        "bairro": data.get("bairro"),
        "cidade": data.get("localidade"),
        "estado": data.get("uf"),
        "endereco_completo": address,
        "lat": lat,
        "lon": lon,
        "image_url": image_url,
        "aviso": "Imagem de mapa/satélite aproximada do endereço — não é uma foto real da fachada (isso exigiria o Google Street View, que é pago).",
    })


@app.route("/api/geoip/<ip>")
def lookup_geoip(ip):
    try:
        r = requests.get(f"http://ip-api.com/json/{ip}", params={"lang": "pt-BR"}, timeout=10)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        return jsonify({"ok": False, "error": f"Falha ao consultar ip-api.com: {e}"}), 502

    if data.get("status") != "success":
        return jsonify({"ok": False, "error": data.get("message", "IP não localizado")}), 404

    lat = data.get("lat")
    lon = data.get("lon")
    filename = "geoip_" + ip.replace(".", "_").replace(":", "_") + ".png"
    try:
        image_url = save_static_map(lat, lon, filename, zoom=12)
    except Exception:
        image_url = None

    return jsonify({
        "ok": True,
        "ip": ip,
        "cidade": data.get("city"),
        "regiao": data.get("regionName"),
        "pais": data.get("country"),
        "isp": data.get("isp"),
        "lat": lat,
        "lon": lon,
        "image_url": image_url,
        "aviso": "Localização aproximada por IP — normalmente só acerta a cidade/região, não o endereço exato.",
    })


TELEGRAM_SESSION = BASE_DIR / "telegram.session"


@app.route("/api/telegram/<phone>")
def lookup_telegram(phone):
    if not TELEGRAM_SESSION.exists():
        return jsonify({
            "ok": False,
            "error": "Telegram não configurado neste computador. Rode 'python telegram_login.py' uma vez (veja README_backend.md).",
        }), 501

    try:
        from telegram_lookup import lookup_phone
    except Exception as e:
        return jsonify({"ok": False, "error": f"Dependência do Telegram não instalada ({e}). Rode: pip install telethon"}), 501

    try:
        result = lookup_phone(phone)
    except Exception as e:
        return jsonify({"ok": False, "error": f"Falha na consulta ao Telegram: {e}"}), 502

    return jsonify(result)


if __name__ == "__main__":
    print("Backend OutraSec rodando em http://localhost:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)
