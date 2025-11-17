import requests
import requests_cache
import csv
import io
import pdfplumber
import re
from app.core.config import settings
from pathlib import Path

CACHE_DIR = Path("/tmp/ffvb_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

requests_cache.install_cache(str(CACHE_DIR / "http_cache"),expire_after=600)

def get_gymnase_address(codmatch, codent):
    url = settings.ffvb_address_url
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {'codmatch': codmatch, 'codent': codent}
    response = requests.post(url, headers=headers, data=data)
    
    if getattr(response, "from_cache", False):
        print(f"[CACHE] Gymnase PDF {codmatch}/{codent}")

    if response.status_code != 200 or response.headers.get('Content-Type') != 'application/pdf':
        print("Erreur lors du téléchargement du PDF.")
        return None

    with pdfplumber.open(io.BytesIO(response.content)) as pdf:
        text = ''
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text += t + '\n'

        match = re.search(r'Salle\s*\n(.*?)(Sol\s*:|Arbitre\.s|$)', text, re.DOTALL)
        if match:
            salle_block = match.group(1)
            lines = [line.strip() for line in salle_block.split('\n') if line.strip()]
            if lines:
                nom = lines[0]
                adresse = ' '.join(lines[1:])
                match_adr = re.search(r"(.+)\s(\d{5})\s(.+)", adresse)
                if match_adr:
                    rue = match_adr.group(1).strip().lower()
                    code_postal = match_adr.group(2)
                    ville = match_adr.group(3).strip()

                    ville = re.sub(r"\s*T[ée]l\.?:.*", "", ville.replace("\\'", "'"), flags=re.I)

                    #print(f"DEBUG: 'nom': {nom}, 'rue': {rue}, 'code_postal': {code_postal}, 'ville': {ville}")

                    return {'nom': nom, 'rue': rue, 'code_postal': code_postal, 'ville': ville}
    return None

def parse_csv_rows(saison,division):

    url = settings.ffvb_csv_url if not division else settings.ffvb_csv_url_division
    saison = saison.replace("-", "/")

    payload = {
        "cnclub": settings.club_id,
        "cal_saison": saison,
        "cal_codent" : "LIIDF",
        "cal_coddiv" : division,
        "typ_edition": "E",
        "type": "RES"
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    print(f"{payload}  -  {url} ==> {headers}")
    response = requests.post(url, data=payload, headers=headers)

    if getattr(response, "from_cache", False):
        print("[CACHE] CSV FFVB")

    response.raise_for_status()
    csv_utf8_str = response.content.decode('latin1').encode('utf-8').decode('utf-8')
    
    return csv.reader(io.StringIO(csv_utf8_str), delimiter=";", quotechar='"')

def parse_local_csv_rows():
    with open("export20242025_utf8.csv", newline="", encoding="utf-8") as csvfile:
        return csv.reader(csvfile, delimiter=";", quotechar='"')

