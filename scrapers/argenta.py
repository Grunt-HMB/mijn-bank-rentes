import pandas as pd
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def scrape_argenta():
    print("Argenta spaarrentes ophalen...")
    url = "https://www.argenta.be/nl/sparen/spaarrekening.html"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")
        soup = BeautifulSoup(page.content(), 'html.parser')
        browser.close()

    # 1. Haal de namen van de rekeningen uit de <thead>
    header_row = soup.find('thead').find('tr')
    rekening_namen = [th.get_text(strip=True) for th in header_row.find_all('th') if th.get_text(strip=True)]

    data = []
    
    # 2. Zoek alle rijen in alle tbodys en identificeer de rijen op tekst
    all_rows = soup.find_all('tr')
    
    basis_vals = []
    getrouw_vals = []
    
    for row in all_rows:
        th = row.find('th')
        if th:
            text = th.get_text(strip=True)
            if "Basisrente" in text:
                basis_vals = [td.get_text(strip=True) for td in row.find_all('td')]
            elif "Getrouwheidspremie" in text:
                getrouw_vals = [td.get_text(strip=True) for td in row.find_all('td')]

    # 3. Koppel alles samen
    if basis_vals and getrouw_vals:
        for i, naam in enumerate(rekening_namen):
            # Pak de rauwe waarden
            raw_basis = basis_vals[i] if i < len(basis_vals) else "0%"
            raw_getrouw = getrouw_vals[i] if i < len(getrouw_vals) else "0%"
            
            # Schoon de tekst op: split op '%', pak het eerste deel en voeg de '%' weer toe
            clean_basis = raw_basis.split('%')[0].strip().replace(',', '.') + " %"
            clean_getrouw = raw_getrouw.split('%')[0].strip().replace(',', '.') + " %"
            
            try:
                # Berekening voor Totaal
                b_val = float(clean_basis.replace('%', ''))
                g_val = float(clean_getrouw.replace('%', ''))
                totaal = f"{(b_val + g_val):.2f}".replace('.', ',') + " %"
            except:
                totaal = "N/B"

            data.append({
                "Bank": "Argenta",
                "Spaarrekening": naam,
                "Basisrente": clean_basis.replace('.', ','),
                "Getrouwheidspremie": clean_getrouw.replace('.', ','),
                "Totale Rente": totaal
            })

    return pd.DataFrame(data)

if __name__ == "__main__":
    df = scrape_argenta()
    print(df.to_string(index=False))