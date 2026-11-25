#!/usr/bin/env python3
"""Locksmith Wars - envoi d'un FBX sur Roblox via l'Assets API d'Open Cloud.

Crée un asset de type Model appartenant au groupe, attend la fin du traitement,
puis affiche et enregistre son assetId dans exports/uploads.json.

Usage :
    uv run scripts/upload_to_roblox.py exports/ORE/ORE_F2.fbx [--name ORE_F2]
    uv run scripts/upload_to_roblox.py exports/SKY/SKY_Warm_SkyboxFt.png --type Decal

--type Decal envoie une image PNG comme Decal (l'ID d'image utilisable par Sky
ou Texture est distinct de l'ID du Decal : le relire dans Studio, Decal.Texture).

La clé API est lue dans la variable d'environnement ROBLOX_API_KEY.
Elle n'est jamais affichée ni écrite dans un fichier.
Aucune dépendance externe (bibliothèque standard uniquement).
"""
import argparse
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.request
import uuid

GROUP_ID = "33016933"  # WingedSword Empire
API = "https://apis.roblox.com/assets/v1"
MAX_SIZE = 20 * 1024 * 1024
UPLOADS_LOG = pathlib.Path("exports/uploads.json")


def multipart(fields, file_field, filename, content, content_type):
    boundary = uuid.uuid4().hex
    chunks = []
    for name, value in fields.items():
        chunks.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode()
        )
    chunks.append(
        (
            f'--{boundary}\r\nContent-Disposition: form-data; name="{file_field}"; '
            f'filename="{filename}"\r\nContent-Type: {content_type}\r\n\r\n'
        ).encode()
    )
    chunks.append(content)
    chunks.append(f"\r\n--{boundary}--\r\n".encode())
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def call(request):
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = response.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as err:
        body = err.read().decode(errors="replace")
        sys.exit(f"Erreur HTTP {err.code} renvoyée par Roblox : {body}")
    except urllib.error.URLError as err:
        sys.exit(f"Impossible de joindre Roblox : {err.reason}")


# type d'asset -> (extension attendue, content type)
ASSET_TYPES = {"Model": (".fbx", "model/fbx"), "Decal": (".png", "image/png")}


def record(name, asset_id, moderation, fbx, asset_type="Model"):
    data = {}
    if UPLOADS_LOG.is_file():
        try:
            data = json.loads(UPLOADS_LOG.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {}
    data[name] = {
        "assetId": asset_id,
        "moderation": moderation,
        "file": str(fbx).replace("\\", "/"),
        "assetType": asset_type,
        "uploadedAt": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    UPLOADS_LOG.parent.mkdir(parents=True, exist_ok=True)
    UPLOADS_LOG.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Envoie un FBX sur Roblox au nom du groupe.")
    parser.add_argument("fbx", help="chemin du fichier .fbx (ou .png avec --type Decal)")
    parser.add_argument("--type", dest="asset_type", choices=sorted(ASSET_TYPES), default="Model",
                        help="type d'asset Roblox (Model par défaut, Decal pour une image PNG)")
    parser.add_argument("--name", help="nom de l'asset (par défaut : nom du fichier)")
    parser.add_argument("--timeout", type=int, default=300, help="attente maximale en secondes")
    args = parser.parse_args()

    api_key = os.environ.get("ROBLOX_API_KEY")
    if not api_key:
        sys.exit("ROBLOX_API_KEY est absente. Voir LISEZMOI_INSTALLATION.txt, étape 3.")

    fbx = pathlib.Path(args.fbx)
    extension, file_content_type = ASSET_TYPES[args.asset_type]
    if not fbx.is_file() or fbx.suffix.lower() != extension:
        sys.exit(f"Fichier {extension} introuvable : {fbx}")
    if fbx.stat().st_size > MAX_SIZE:
        sys.exit("Fichier trop gros (20 Mo maximum par asset).")

    name = args.name or fbx.stem
    request_json = {
        "assetType": args.asset_type,
        "displayName": name,
        "description": f"Locksmith Wars - {name}",
        "creationContext": {"creator": {"groupId": GROUP_ID}},
    }
    body, content_type = multipart(
        {"request": json.dumps(request_json)}, "fileContent", fbx.name, fbx.read_bytes(), file_content_type
    )
    create = urllib.request.Request(
        f"{API}/assets", data=body, method="POST",
        headers={"x-api-key": api_key, "Content-Type": content_type},
    )
    operation = call(create)
    op_path = operation.get("path")
    if not op_path:
        sys.exit(f"Réponse inattendue de Roblox : {json.dumps(operation)}")

    deadline = time.time() + args.timeout
    while time.time() < deadline:
        status = call(urllib.request.Request(f"{API}/{op_path}", headers={"x-api-key": api_key}))
        if status.get("done"):
            if "response" not in status:
                sys.exit(f"Échec du traitement : {json.dumps(status.get('error', status))}")
            asset = status["response"]
            asset_id = str(asset.get("assetId"))
            moderation = asset.get("moderationResult", {}).get("moderationState", "inconnu")
            record(name, asset_id, moderation, fbx, args.asset_type)
            print(json.dumps({"name": name, "assetId": asset_id, "moderation": moderation}))
            return
        time.sleep(3)
    sys.exit(f"Délai dépassé : l'opération {op_path} n'est pas terminée. Réessayer plus tard.")


if __name__ == "__main__":
    main()
