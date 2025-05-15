import asyncio
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
from playwright.async_api import async_playwright, TimeoutError

def get_test_date_range():
    # Testing with April 2025
    start = "01-04-2025"
    end = "30-04-2025"
    label = "2025-04"
    return start, end, label

def parse_customer_report_json(data: dict) -> pd.DataFrame:
    rows = []
    for customer in data.get("data", []):
        row = {}
        for item in customer:
            key = item.get("Key")
            value = item.get("Value")
            row[key] = value
        rows.append(row)
    return pd.DataFrame(rows)


async def fetch_and_save_single_month_report_via_api(page, login_data):
    from_date = "01-04-2025"
    to_date = "30-04-2025"
    label = "2025-04"

    url = (
        "https://login.dreamteamaffiliates.com/affiliates//Reports/customerReportingReport"
        f"?playerID=&websiteID=All&username=&productID=All&customerTypeID=All&rewardPlanId=All&countryId=All"
        f"&FilterBySignUpDate=0&FilterByActivityDate=1&FilterbyExpirationDate=0"
        f"&FilterByActivityDateFrom={from_date}&FilterByActivityDateTo={to_date}"
        f"&FilterBySignUpDateFrom={from_date}&FilterBySignUpDateTo={to_date}"
        f"&FilterByExpirationDateFrom={from_date}&FilterByExpirationDateTo={to_date}&customerSource=All"
    )

    print(f"📡 Requesting report data for: {label}")
    
    response = await page.request.get(url)
    
    if response.status != 200:
        print(f"❌ Failed to fetch data — status code {response.status}")
        return

    json_data = await response.json()

    # Parse JSON into flat rows
    df = parse_customer_report_json(json_data)

    folder = Path(f"./data/{login_data['account_name']}")
    folder.mkdir(parents=True, exist_ok=True)
    df.to_csv(folder / f"{label}.csv", index=False)
    print(f"✅ Saved API data: {folder / f'{label}.csv'}")


async def run():
    login_path = Path("accounts/dta_logins.json")
    with open(login_path, "r") as f:
        dta_logins = json.load(f)

    login_data = dta_logins[0]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
            )
        )
        await context.add_init_script(
            """Object.defineProperty(navigator, 'webdriver', { get: () => undefined })"""
        )

        page = await context.new_page()

        print(f"Navigating to {login_data['login_url']}")
        await page.goto(login_data["login_url"], wait_until="networkidle")
        await page.wait_for_timeout(5000)

        try:
            await page.fill('#txtUsername', login_data["username"])
            await page.fill('#txtPassword', login_data["password"])
            await page.click('#btnLogin')
            await page.wait_for_load_state("networkidle")

            if "dashboard" in page.url.lower():
                print(f"✅ Login successful! Now at: {page.url}")
            else:
                print(f"❌ Possibly failed login. Current URL: {page.url}")

        except TimeoutError:
            print("❌ Login form not found, saving page...")
            with open("debug_page.html", "w", encoding="utf-8") as f:
                f.write(await page.content())
            return

        # Handle modal
        try:
            await page.wait_for_selector('button[data-bb-handler="close"]', timeout=5000)
            await page.click('button[data-bb-handler="close"]')
            print("✅ Modal closed")
        except TimeoutError:
            print("⚠️ Modal not found — continuing")

        # Test single-month report fetch
        await fetch_and_save_single_month_report_via_api(page, login_data)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
