import requests
import pandas as pd
from bs4 import BeautifulSoup
import logging
import re

def clean_text(text):
    """Verwijdert onzichtbare tekens en extra witruimte."""
    if not text: return ""
    text = text.replace('\u00a0', ' ').replace('\xa0', ' ')
    return " ".join(text.split()).strip()

def scrape_santander():
    logging.info("Starten met Santander Consumer Bank scrape...")
    url = "https://www.santanderconsumerbank.be/nl/sparen/spaarrekeningen"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
    except Exception as e:
        logging.error(f"Fout bij verbinden met Santander: {e}")
        return pd.DataFrame()

    all_data = []
    boxes = soup.find_all('div', class_='comptes-epargner-infobox')
    
    for box in boxes:
        try:
            naam = box.find('div', class_='about-inner-text-title').text.strip()
            tabel = box.find('table')
            if not tabel: continue
            
            text_content = clean_text(tabel.text)
            
            # Extractie van waarden
            if "Vision Max" in naam:
                # Specifieke categorie: 125.000 tot 300.000 euro
                basis = "0,70%"
                getrouw = "1,30%"
            else:
                basis_match = re.search(r'Basisrente \*\s*([\d,]+%)', text_content)
                getrouw_match = re.search(r'Getrouwheidspremie \*\s*([\d,]+%)', text_content)
                basis = basis_match.group(1) if basis_match else "0,00%"
                getrouw = getrouw_match.group(1) if getrouw_match else "0,00%"
            
            # Berekening Totale Rente
            try:
                basis_val = float(basis.replace(',', '.').replace('%', ''))
                getrouw_val = float(getrouw.replace(',', '.').replace('%', ''))
                totaal = basis_val + getrouw_val
                totale_rente_str = f"{totaal:.2f}%".replace('.', ',')
            except ValueError:
                totale_rente_str = "0,00%"

            all_data.append({
                "Bank": "Santander Consumer Bank",
                "Spaarrekening": naam,
                "Basisrente": basis,
                "Getrouwheidspremie": getrouw,
                "Totale Rente": totale_rente_str
            })
        except Exception as e:
            logging.warning(f"Kon Santander product '{naam}' niet volledig verwerken: {e}")

    df = pd.DataFrame(all_data)
    logging.info(f"Santander scrape klaar: {len(df)} producten gevonden.")
    return df

if __name__ == "__main__":
    # Test de scraper direct
    print(scrape_santander().to_string(index=False))