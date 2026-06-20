import pandas as pd
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def scrape_cph():
    print("CPH Bank spaarrentes ophalen...")
    url = "https://www.cph.be/epargner/comptes-depargne-reglementes-commercialises-par-la-banque-cph/"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")
        
        # Wacht tot de tabel daadwerkelijk in de DOM aanwezig is
        page.wait_for_selector("table")
        soup = BeautifulSoup(page.content(), 'html.parser')
        browser.close()

    data = []
    
    # Zoek alle tabellen
    tables = soup.find_all('table')
    
    for table in tables:
        # We zoeken rijen (tr) die de rentepercentages bevatten.
        # Deze rijen bevatten altijd het woord 'basis' of 'fidélité' of een '%'.
        rows = table.find_all('tr')
        current_product = None
        
        for row in rows:
            # Detecteer productnaam (headers met colspan="5")
            header = row.find('th', {'colspan': '5'})
            if header:
                current_product = header.get_text(strip=True)
                continue
            
            # Detecteer rijen met rente (check op aanwezigheid van %)
            cells = row.find_all('td')
            if current_product and len(cells) >= 3 and "%" in row.get_text():
                # We pakken de tekst van de cellen
                basis = cells[1].get_text(strip=True).replace('sur base annuelle', '').strip()
                getrouw = cells[2].get_text(strip=True).replace('sur base annuelle', '').strip()
                totaal = cells[3].get_text(strip=True).replace('sur base annuelle', '').strip()
                
                data.append({
                    "Bank": "CPH Bank",
                    "Spaarrekening": current_product,
                    "Basisrente": basis,
                    "Getrouwheidspremie": getrouw,
                    "Totale Rente": totaal
                })

    return pd.DataFrame(data)

if __name__ == "__main__":
    df = scrape_cph()
    if df.empty:
        print("FOUT: Geen data gevonden. De structuur van de pagina is mogelijk veranderd.")
    else:
        print(df.to_string(index=False))