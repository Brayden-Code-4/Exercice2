import os
import base64
import requests
from pathlib import Path

API_BASE = "https://api.rodiumai.io/v1"
TIMEOUT_CHAT_IMAGE = 60
TIMEOUT_VIDEO = 150

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

API_KEY = os.getenv("RODIUMAI_API_KEY")
if not API_KEY:
    print("ERREUR: RODIUMAI_API_KEY manquant. Fais: $env:RODIUMAI_API_KEY='ta_cle' en PowerShell")
    exit(1)

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def handle_error(resp):
    if resp.status_code != 200:
        try:
            data = resp.json()
            code = data.get("error", {}).get("code") or data.get("code") or "unknown"
            msg = data.get("error", {}).get("message") or data.get("message") or resp.text
        except:
            code = "unknown"
            msg = resp.text
        print(f"\n[ERREUR {resp.status_code}] Code: {code} | Message: {msg}")
        return False
    return True

def etape_1_chat():
    while True:
        print("\n Étape 1 : Chat ")
        question = input("Votre question : ").strip()
        if not question:
            continue
        payload = {
            "model": "openai/gpt-4o",
            "messages": [{"role": "user", "content": question}]
        }
        try:
            r = requests.post(f"{API_BASE}/chat/completions", json=payload, headers=HEADERS, timeout=TIMEOUT_CHAT_IMAGE)
            if not handle_error(r):
                continue
            data = r.json()
            print(f"\n{data['choices'][0]['message']['content']}")
            print(f"\nCoût : {data.get('cost_rodi', 'N/A')} RODI")
        except Exception as e:
            print(f"Exception: {e}")

        c = input("\nRester sur cette étape (r) ou passer à la suivante (s) ? ").lower()
        if c == 's': return 'next'
        if c == 'q': return 'quit'

def etape_2_image():
    while True:
        print("\n Étape 2 : Image ")
        prompt = input("Décrivez l'image : ").strip()
        if not prompt: continue
        payload = {"model": "openai/gpt-image-1-mini", "prompt": prompt, "size": "1024x1024"}
        try:
            r = requests.post(f"{API_BASE}/images/generations", json=payload, headers=HEADERS, timeout=TIMEOUT_CHAT_IMAGE)
            if not handle_error(r):
                c = input("Revenir (b), rester (r), quitter (q) ? ").lower()
                if c == 'b': return 'back'
                if c == 'q': return 'quit'
                continue
            data = r.json()
            Path("image.png").write_bytes(base64.b64decode(data["data"][0]["b64_json"]))
            print("Image enregistrée : image.png")
            print(f"Coût : {data.get('cost_rodi', 'N/A')} RODI")
        except Exception as e:
            print(f"Exception: {e}")

        c = input("\nRevenir en arrière (b), rester (r) ou passer à la suivante (s) ? ").lower()
        if c == 's': return 'next'
        if c == 'b': return 'back'
        if c == 'q': return 'quit'

def etape_3_video():
    while True:
        print("\n Étape 3 : Vidéo ")
        prompt = input("Décrivez la vidéo (courte 4s) : ").strip()
        if not prompt: continue
        payload = {"model": "openai/sora-2", "prompt": prompt, "duration_seconds": 4, "size": "720x1280"}
        try:
            r = requests.post(f"{API_BASE}/videos/generations", json=payload, headers=HEADERS, timeout=TIMEOUT_VIDEO)
            if not handle_error(r):
                c = input("Revenir (b), rester (r), quitter (q) ? ").lower()
                if c == 'b': return 'back'
                if c == 'q': return 'quit'
                continue
            data = r.json()
            if "data" in data and "b64_json" in data["data"][0]:
                Path("video.mp4").write_bytes(base64.b64decode(data["data"][0]["b64_json"]))
            elif "data" in data and "url" in data["data"][0]:
                vr = requests.get(data["data"][0]["url"], timeout=60)
                Path("video.mp4").write_bytes(vr.content)
            else:
                Path("video.mp4").write_bytes(r.content)
            print("Vidéo enregistrée : video.mp4")
        except Exception as e:
            print(f"Exception: {e}")

        c = input("\nRevenir en arrière (b), rester (r) ou quitter (q) ? ").lower()
        if c == 'b': return 'back'
        return 'quit'

etape = 1
while True:
    if etape == 1:
        res = etape_1_chat()
        if res == 'next': etape = 2
        else: break
    elif etape == 2:
        res = etape_2_image()
        if res == 'next': etape = 3
        elif res == 'back': etape = 1
        else: break
    elif etape == 3:
        res = etape_3_video()
        if res == 'back': etape = 2
        else: break