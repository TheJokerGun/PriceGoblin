# Weekly Status Report: PriceGoblin

## ✅ Accomplished This Week
*   **Backend Product API Expanded**: Added/solidified product detail, current-price, and check-price endpoint flow for tracked products.
*   **Tracking Management Added**: Implemented tracking route/service support for listing tracking entries, deleting entries, and toggling active/inactive status.
*   **Scraper Layer Refactor**: Refactored scraper service and improved URL/category scraper structure for better integration with product + tracking flows.
*   **API/Dev Docs Updated**: Updated API contract and added endpoint testing guide for Swagger/curl based backend validation.
*   **Frontend Product Detail View**: Added product page with price history graph display.
*   **Frontend Tracking UX Improvements**: Added tracking list handling, active status toggles, and delete action in frontend views.
*   **Frontend Category Input Work Started**: Added category selector and related frontend type refactoring.
*   **Auth UI Flow Extended**: Added register/login related frontend flow improvements tied to user tracking list behavior.

## 📅 Planned for Next Week
*   **Finish + Test Category Search**: Complete category search end-to-end (frontend + backend integration) and test result quality/usability.
*   **Price Check Trigger in Frontend**: Finish frontend support for explicit price-check action per tracked product.
*   **Price Alert/Notification Feature**: Implement initial alert flow so users can define a target price and receive a notification-style signal when price drops below that threshold.
*   **Testing Focus**: Add and run endpoint tests for auth/products/tracking/scraper flows to replace current mostly manual testing.
