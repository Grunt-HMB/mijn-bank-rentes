import requests
import pandas as pd
from bs4 import BeautifulSoup
import json
import re
import logging

# Log configuratie: logt naar 'scraper.log'
logging.basicConfig(
    filename='scraper.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def clean_text(text):
    """IJzeren bezem voor data: verwijdert alle rommel en \u00a0 tekens."""
    if not text: return ""
    text = text.replace('\u00a0', ' ').replace('\xa0', ' ').replace('op jaarbasis', '')
    # Gebruik regex om alleen het percentage-formaat (bijv. 0,15%) te behouden
    match = re.search(r'(\d+,\d+)\s*%', text)
    if match:
        return match.group(1) + "%"
    return " ".join(text.split()).strip()

def scrape_ing_api():
    logging.info("Starten met ING België scrape...")
    url = "https://api.www.ing.be/be/public/pagemodel?pageUrl=/nl/particulieren/sparen/gereglementeerde-ing-spaarrekeningen"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        logging.info("Data succesvol opgehaald van API.")
    except Exception as e:
        logging.error(f"Fout bij verbinden met ING API: {e}")
        return pd.DataFrame()

    all_data = []
    soup = BeautifulSoup(json.dumps(data), 'html.parser')
    titels = soup.find_all(['h3', 'strong'])
    ongewenste_termen = ['Categorie', 'Basisrente', 'Getrouwheidspremie', 'Toepasselijke voorwaarden', 'Optelling', 'Opgelet']
    
    for titel_tag in titels:
        tekst = " ".join(titel_tag.text.split())
        if any(term in tekst for term in ongewenste_termen) or len(tekst) < 3:
            continue
            
        tabel = titel_tag.find_next('table')
        if not tabel:
            continue
            
        product_naam = tekst.replace(' - niet gecommercialiseerd', '').strip()
        logging.info(f"Verwerken product: {product_naam}")
        
        for row in tabel.find_all('tr'):
            cols = row.find_all('td')
            if len(cols) >= 4:
                basis = clean_text(cols[1].text)
                getrouw = clean_text(cols[2].text)
                totaal = clean_text(cols[3].text)
                
                if "%" in basis:
                    all_data.append({
                        "Bank": "ING België",
                        "Spaarrekening": product_naam,
                        "Basisrente": basis,
                        "Getrouwheidspremie": getrouw,
                        "Totale Rente": totaal
                    })

    df = pd.DataFrame(all_data)
    if not df.empty:
        df = df.drop_duplicates()
        logging.info(f"Scrape voltooid. {len(df)} rijen gevonden.")
    else:
        logging.warning("Geen data gevonden om op te slaan.")
        
    return df

if __name__ == "__main__":
    df = scrape_ing_api()
    if not df.empty:
        print(df.to_string(index=False))
        df.to_csv("ING_Rentes.csv", sep=';', index=False, encoding='utf-8-sig')
    else:
        print("Geen data gevonden.")