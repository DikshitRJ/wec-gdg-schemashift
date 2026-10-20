# Database Schema Similarity Report

**Overall Match:** `93.5%` (MATCHED)
- Matched: `31`
- Guessed: `7`
- Needs Review: `0`

## Per-Entity Alignment

| Collection | Target Tables | Match % | Fields | Matched | Guessed | Needs Review |
|---|---|---|---|---|---|---|
| `orders` | `orders, orders_items` | `94.5%` | 13 | 12 | 1 | 0 |
| `products` | `products, products_categories` | `96.3%` | 7 | 6 | 1 | 0 |
| `reviews` | `reviews` | `92.6%` | 6 | 4 | 2 | 0 |
| `users` | `users, users_tags` | `91.3%` | 12 | 9 | 3 | 0 |

## Top Score Drags (Ambiguous / Divergent Fields)

| Source Field | Target Column | Score | Band | Reasons |
|---|---|---|---|---|
| `userId` | `orders.user_id` | `75.5%` | `guessed` | None |
| `userId` | `reviews.user_id` | `75.5%` | `guessed` | None |
| `tags[]` | `users_tags.value` | `78.3%` | `guessed` | None |
| `rating` | `reviews.rating` | `80.0%` | `guessed` | TYPE_PURITY_LOW |
| `categories[]` | `products_categories.value` | `80.0%` | `guessed` | None |
| `address.city` | `users.address_city` | `82.5%` | `guessed` | None |
| `address.zip` | `users.address_zip` | `82.5%` | `guessed` | None |
