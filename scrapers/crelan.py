import pandas as pd
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def scrape_crelan():
    print("Crelan spaarrentes ophalen...")
    url = "https://www.crelan.be/nl/particulieren/sparen-en-beleggen/sparen/product/spaarrekeningen"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")
        soup = BeautifulSoup(page.content(), 'html.parser')
        browser.close()

    thead = soup.find('thead', class_='table__head')
    headers = [th.get_text(strip=True) for th in thead.find_all('th') if th.get_text(strip=True)]
    rekening_namen = headers

    data = []
    tbody = soup.find('tbody', class_='table__body')
    rows = tbody.find_all('tr', class_='table__row')
    
    basis_vals = []
    getrouw_vals = []
    
    for row in rows:
        th = row.find('th')
        if not th: continue
        label = th.get_text(strip=True)
        
        # We pakken enkel de tekst uit de 'tablesaw-cell-content' span
        values = [td.find('span', class_='tablesaw-cell-content').get_text(strip=True) 
                  for td in row.find_all('td')]
        
        if "Basisrente" in label:
            basis_vals = values
        elif "Getrouwheidspremie" in label:
            getrouw_vals = values

    # Koppelen en opschonen
    for i, naam in enumerate(rekening_namen):
        raw_basis = basis_vals[i] if i < len(basis_vals) else "0%"
        raw_getrouw = getrouw_vals[i] if i < len(getrouw_vals) else "0%"
        
        # Berekening
        try:
            b_val = float(raw_basis.replace('%', '').replace(',', '.'))
            g_val = float(raw_getrouw.replace('%', '').replace(',', '.'))
            totaal = f"{(b_val + g_val):.2f}".replace('.', ',') + " %"
        except:
            totaal = "N/B"
            
        data.append({
            "Bank": "Crelan",
            "Spaarrekening": naam,
            "Basisrente": raw_basis,
            "Getrouwheidspremie": raw_getrouw,
            "Totale Rente": totaal
        })

    return pd.DataFrame(data)

if __name__ == "__main__":
    df = scrape_crelan()
    print(df.to_string(index=False))