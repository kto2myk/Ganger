# Ganger Frontend (Next.js Skeleton)

This is the Next.js (App Router) skeleton mirroring existing server-side templates.

## Route Mapping

| Old Template                | New Path                        |
|-----------------------------|---------------------------------|
| home.html                   | /                               |
| login.html                  | /login                          |
| signup.html                 | /signup                         |
| password_reset.html         | /password/reset                 |
| my_info.html                | /me                             |
| my_profile.html             | /profile/[username]             |
| search_page.html            | /search                         |
| shop_page.html              | /shop                           |
| shop_categorized_page.html  | /shop/category/[category]       |
| display_product.html        | /product/[id]                   |
| display_cart.html           | /cart                           |
| after_add_cart.html         | /cart/added                     |
| shopping_page.html          | /checkout                       |
| complete_checkout.html      | /checkout/complete              |
| create_post.html            | /post/create                    |
| display_post.html           | /post/[id]                      |
| test_post.html              | /post/test                      |
| create_design.html          | /design/create                  |
| image_display.html          | /image/[id]                     |
| display_notification.html   | /notifications                  |
| display_message_rooms.html  | /messages                       |
| message_room.html           | /messages/[roomId]              |
| error.html                  | /error                          |

## Getting Started

1. Install dependencies:
```bash
cd frontend
npm install
```
2. Run dev server:
```bash
npm run dev
```
3. Open http://localhost:3000

## Backend Integration
Set `NEXT_PUBLIC_API_BASE_URL` in a `.env.local` pointing to the existing Python backend (e.g. `http://localhost:8000`). Use functions in `lib/api.ts`.

## Next Steps
1. Implement auth (e.g. next-auth) + session handling.
2. Replace placeholder pages with UI + data fetching.
3. Add component library / styling (Tailwind, etc.).
4. Introduce proper error boundary & loading UI (loading.tsx / error.tsx per route).
5. Add real-time messaging (WebSocket provider) for /messages.

---
Skeleton generated for refactoring migration.
