import pandas as pd
from playwright.sync_api import sync_playwright
import io


def scrape():
    url = "https://www.belfius.be/site/retail/nl/producten/sparen/gereglementeerde-spaarrekeningen"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")

        tabel_html = page.locator("table.basic-table").first.evaluate("el => el.outerHTML")
        browser.close()

    df = pd.read_html(io.StringIO(tabel_html))[0]

    df = df[
        [
            "Rekening",
            "Basisrente",
            "Getrouwheidspremie",
            "Optelling van basisrente en getrouwheidspremie",
        ]
    ]

    df.columns = [
        "Spaarrekening",
        "Basisrente",
        "Getrouwheidspremie",
        "Totale Rente",
    ]

    df.insert(0, "Bank", "Belfius")

    def clean_percentage(val):
        return str(val).split("%")[0].strip().replace(".", ",") + "%"

    for col in ["Basisrente", "Getrouwheidspremie", "Totale Rente"]:
        df[col] = df[col].apply(clean_percentage)

    return df


if __name__ == "__main__":
    belfius_data = scrape()
    print(belfius_data)