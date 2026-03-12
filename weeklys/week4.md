# Weekly Status Report: PriceGoblin

## ✅ Accomplished This Week
*   **Locale-aware auth + scraping**: Added locale to JWT, stored user locale, and wired locale into Accept-Language and Playwright contexts for scrapers.
*   **Image URL support end-to-end**: Products now capture image URLs during URL and category scraping, with DB/schema support.
*   **URL scraping expanded**: Improved coverage for major retailers (Amazon, eBay, IKEA, AliExpress, Cyberport, notebooksbilliger) plus Steam, Geizhals, TCGplayer, and Keyforsteam. Added unsupported-site handling for sites blocked by anti-bot (e.g., Etsy/Cardmarket URL scraping).
*   **Category scraping improvements**: Added/expanded game and cards category providers (Steam, Keyforsteam, Cardmarket, TCGplayer) and bulk selection workflow support.
*   **Backend maintenance + docs**: Added project overview documentation and a safer data reset script with optional user wipe.
*   **Frontend enhancements merged**: Dashboard + product detail UI, product search/selection components, global error handling, product images, alert UX, theme toggle, and locale-aware currency/date formatting.

## 📅 Planned for Next Week
*   **Price alert delivery**: Decide notification channel (email/Teams) and implement first working alert pipeline.
*   **Testing focus**: Add automated tests for auth, locale handling, and scraper flows; reduce reliance on manual checks.
*   **Refactoring and documentation**: Focus on Refactoring and commenting code, as well as documenting the Project.

