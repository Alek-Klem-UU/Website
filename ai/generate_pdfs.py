import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

async def html_to_pdf(html_path: str, pdf_path: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(f"file:///{html_path}", wait_until="networkidle")
        await page.pdf(
            path=pdf_path,
            format="A4",
            print_background=True,
            display_header_footer=False,
            margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
        )
        await browser.close()
        print(f"Saved: {pdf_path}")

async def main():
    base = Path(r"C:\Users\Alek\ai")
    await html_to_pdf(str(base / "cv.html"), str(base / "cv.pdf"))
    await html_to_pdf(str(base / "cv-nl.html"), str(base / "cv-nl.pdf"))

asyncio.run(main())
