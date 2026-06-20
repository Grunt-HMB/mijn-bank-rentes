import pandas as pd
import re
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def scrape_nibc():
    url = "https://www.nibc.be/nl/spaarproducten/"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")
        soup = BeautifulSoup(page.content(), 'html.parser')
        browser.close()

    table = soup.find('table')
    if not table: return None
    
    data = []
    
    # Verbeterde header extractie: pakt alle tekst uit de header en voegt ze samen tot één regel
    headers = []
    for th in table.find('thead').find_all('th'):
        # Pakt tekst uit alle <p> tags binnen de th en voegt ze samen met een spatie
        header_text = " ".join([p.get_text(strip=True) for p in th.find_all('p')])
        headers.append(header_text)
        
    rente_rij = table.find('tbody').find_all('tr')[2].find_all('td')
    
    for i, col in enumerate(rente_rij):
        naam = headers[i]
        
        # Filter de termijnrekening eruit
        if "Termijnrekening" in naam:
            continue
            
        tekst = col.get_text(" ", strip=True)
        percentages = re.findall(r'(\d+(?:,\d+)?)\s?%', tekst)
        
        basis = float(percentages[0].replace(',', '.')) if len(percentages) > 0 else 0.0
        getrouw = float(percentages[1].replace(',', '.')) if len(percentages) > 1 else 0.0
        totaal = basis + getrouw
        
        data.append({
            "Bank": "NIBC",  # <--- DIT IS DE NIEUWE KOLOM
            "Spaarrekening": naam,
            "Basisrente": f"{basis:.2f}%".replace('.', ','),
            "Getrouwheidspremie": f"{getrouw:.2f}%".replace('.', ','),
            "Totale Rente": f"{basis + getrouw:.2f}%".replace('.', ',')
        })

    return pd.DataFrame(data)

if __name__ == "__main__":
    df = scrape_nibc()
    print(df.to_string(index=False))