import pandas as pd
import re
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def scrape_medirect_volledig():
    url = "https://www.medirect.be/nl-be/vergelijking-van-spaarrekeningen/"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")
        html = page.content()
        browser.close()

    soup = BeautifulSoup(html, 'html.parser')
    
    # We selecteren alle relevante elementen in de volgorde waarin ze op de pagina staan
    # Dit pakt zowel de titels (spans/h3) als alle tekstblokken (p)
    elementen = soup.select('.elementor-button-text.text-gray-900.font-semibold.text-base, .elementor-heading-title, p')
    
    data = []
    current_product = None
    temp_percentages = []

    for el in elementen:
        tekst = el.get_text(strip=True)
        
        # Check of dit een productnaam is
        if "MeDirect" in tekst and ("Sparen" in tekst or "Max" in tekst):
            # Als we al een product aan het verwerken waren, sla die op
            if current_product and len(temp_percentages) >= 3:
                data.append({
		    "Bank": "Medirect",  # <--- DIT IS DE NIEUWE KOLOM
                    "Spaarrekening": current_product,
                    "Basisrente": temp_percentages[0],
                    "Getrouwheidspremie": temp_percentages[1],
                    "Totale Rente": temp_percentages[2]
                })
            
            # Start nieuw product
            current_product = tekst
            temp_percentages = []
            
        # Check of dit een percentage is (bevat '%')
        elif '%' in tekst and current_product:
            # We filteren alleen de tekst met het percentage erin
            match = re.search(r'(\d+(?:,\d+)?\s?%)', tekst)
            if match:
                temp_percentages.append(match.group(1))

    # Voeg de laatste toe na de loop
    if current_product and len(temp_percentages) >= 3:
        data.append({
            "Bank": "Medirect",  # <--- DIT IS DE NIEUWE KOLOM
            "Spaarrekening": current_product,
            "Basisrente": temp_percentages[0],
            "Getrouwheidspremie": temp_percentages[1],
            "Totale Rente": temp_percentages[2]
        })


    return pd.DataFrame(data)

if __name__ == "__main__":
    df = scrape_medirect_volledig()
    if not df.empty:
        df.to_excel("spaarrentes_medirect.xlsx", index=False)
        print("Data succesvol gescraped:")
        print(df.to_string(index=False))
    else:
        print("Geen data gevonden. De structuur kwam niet overeen.")