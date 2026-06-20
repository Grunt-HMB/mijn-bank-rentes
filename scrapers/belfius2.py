import pandas as pd
from playwright.sync_api import sync_playwright
import io

def get_belfius_data():
    url = "https://www.belfius.be/site/retail/nl/producten/sparen/gereglementeerde-spaarrekeningen"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")
        
        # We pakken de tabel op basis van de klasse
        tabel_html = page.locator("table.basic-table").first.evaluate("el => el.outerHTML")
        browser.close()

    # Lees de tabel
    df = pd.read_html(io.StringIO(tabel_html))[0]

    # Opschonen van de data naar jouw gewenste formaat
    # 1. Selecteer en hernoem kolommen
    df = df[['Rekening', 'Basisrente', 'Getrouwheidspremie', 'Optelling van basisrente en getrouwheidspremie']]
    df.columns = ['Spaarrekening', 'Basisrente', 'Getrouwheidspremie', 'Totale Rente']
    
    # 2. Voeg de banknaam toe
    df.insert(0, 'Bank', 'Belfius')
    
    # 3. Functie om "op jaarbasis" te verwijderen en komma te behouden voor Excel
    def clean_percentage(val):
        return str(val).split('%')[0].strip().replace('.', ',') + '%'

    for col in ['Basisrente', 'Getrouwheidspremie', 'Totale Rente']:
        df[col] = df[col].apply(clean_percentage)

    return df

# Data ophalen
belfius_data = get_belfius_data()

# Appendeer aan je bestaande CSV/Excel
# Als je een CSV hebt:
# belfius_data.to_csv("alle_bankrentes_master.csv", mode='a', header=False, index=False, sep=';')

print(belfius_data)