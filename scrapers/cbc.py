import pandas as pd
from playwright.sync_api import sync_playwright

def scrape_cbc():
    print("CBC spaarrentes ophalen...")
    # De Franstalige URL van CBC
    url = "https://www.cbc.be/particuliers/fr/epargner/comptes-epargne-reglementes.html"
    data = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(url, wait_until="networkidle", timeout=60000)
            page.wait_for_selector("table", timeout=15000)
            
            tabel_containers = page.query_selector_all("div[data-component-type='table']")
            
            for container in tabel_containers:
                table = container.query_selector("table")
                if not table: continue
                
                # Titel ophalen
                titel_element = table.evaluate_handle("el => el.querySelector('b')")
                titel = titel_element.evaluate("el => el.innerText") if titel_element else "CBC Compte d'épargne"
                
                rows = table.query_selector_all("tr")
                for row in rows:
                    cols = row.query_selector_all("td")
                    if len(cols) >= 3:
                        text_basis = cols[1].inner_text()
                        if "%" in text_basis:
                            # Opschonen (franstalig: 'sur base annuelle')
                            basis_raw = text_basis.replace('sur base annuelle', '').strip()
                            getrouw_raw = cols[2].inner_text().replace('sur base annuelle', '').strip()
                            
                            # Berekening
                            try:
                                b_val = float(basis_raw.replace('%', '').replace(',', '.'))
                                g_val = float(getrouw_raw.replace('%', '').replace(',', '.'))
                                totaal = f"{(b_val + g_val):.2f}".replace('.', ',') + "%"
                            except:
                                totaal = "N/B"
                                
                            data.append({
                                "Bank": "CBC",
                                "Spaarrekening": str(titel).strip(),
                                "Basisrente": basis_raw,
                                "Getrouwheidspremie": getrouw_raw,
                                "Totale Rente": totaal
                            })
        except Exception as e:
            print(f"Fout tijdens CBC scraping: {e}")
        finally:
            browser.close()
            
    return pd.DataFrame(data)

if __name__ == "__main__":
    df = scrape_cbc()
    print(df.to_string(index=False))