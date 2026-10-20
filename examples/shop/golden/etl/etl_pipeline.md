# ETL Migration Pipeline Plan

**Source Database:** `shop`
**Schema Map Hash:** `sha256:a6dfb0cbaaa0ab1359eb734eda0c7299de6dff4cc78daf6700c410ab03f866e6` (v1)

## Execution Order (Topological)

### 1. Table `products` (root)
- **Source Collection:** `products`

| Column | PostgreSQL Type | Source Path | Transform | Nullable |
|---|---|---|---|---|
| `id` | `CHAR(24)` | `_id` | `objectid_hex` | False |
| `attrs` | `JSONB` | `attrs` | `json_dump` | False |
| `description` | `TEXT` | `description` | `identity` | False |
| `in_stock` | `BOOLEAN` | `inStock` | `identity` | False |
| `name` | `TEXT` | `name` | `identity` | False |
| `price` | `NUMERIC(12,2)` | `price` | `decimal_numeric` | False |
| `sku` | `TEXT` | `sku` | `identity` | False |

### 2. Table `products_categories` (child)
- **Source Collection:** `products`
- **Array Expansion Path:** `categories[]`

| Column | PostgreSQL Type | Source Path | Transform | Nullable |
|---|---|---|---|---|
| `id` | `BIGINT` | `-` | `identity` | False |
| `product_id` | `CHAR(24)` | `_id` | `objectid_hex` | False |
| `position` | `INTEGER` | `$index` | `identity` | False |
| `value` | `TEXT` | `categories[]` | `identity` | False |

### 3. Table `users` (root)
- **Source Collection:** `users`

| Column | PostgreSQL Type | Source Path | Transform | Nullable |
|---|---|---|---|---|
| `id` | `CHAR(24)` | `_id` | `objectid_hex` | False |
| `address_city` | `TEXT` | `address.city` | `identity` | False |
| `address_geo_lat` | `DOUBLE PRECISION` | `address.geo.lat` | `identity` | False |
| `address_geo_lng` | `DOUBLE PRECISION` | `address.geo.lng` | `identity` | False |
| `address_state` | `TEXT` | `address.state` | `identity` | False |
| `address_street` | `TEXT` | `address.street` | `identity` | False |
| `address_zip` | `TEXT` | `address.zip` | `identity` | False |
| `created_at` | `TIMESTAMPTZ` | `createdAt` | `date_utc` | False |
| `email` | `TEXT` | `email` | `identity` | False |
| `name` | `TEXT` | `name` | `identity` | False |
| `prefs_newsletter` | `BOOLEAN` | `prefs.newsletter` | `identity` | False |
| `prefs_theme` | `TEXT` | `prefs.theme` | `identity` | False |

### 4. Table `orders` (root)
- **Source Collection:** `orders`

| Column | PostgreSQL Type | Source Path | Transform | Nullable |
|---|---|---|---|---|
| `id` | `CHAR(24)` | `_id` | `objectid_hex` | False |
| `coupon_code` | `TEXT` | `couponCode` | `identity` | True |
| `created_at` | `TIMESTAMPTZ` | `createdAt` | `date_utc` | False |
| `shipping_address_city` | `TEXT` | `shipping.address.city` | `identity` | False |
| `shipping_address_state` | `TEXT` | `shipping.address.state` | `identity` | False |
| `shipping_address_street` | `TEXT` | `shipping.address.street` | `identity` | False |
| `shipping_address_zip` | `TEXT` | `shipping.address.zip` | `identity` | False |
| `shipping_carrier` | `TEXT` | `shipping.carrier` | `identity` | False |
| `shipping_tracking_no` | `TEXT` | `shipping.trackingNo` | `identity` | False |
| `status` | `TEXT` | `status` | `identity` | False |
| `user_id` | `CHAR(24)` | `userId` | `objectid_hex` | False |

### 5. Table `orders_items` (child)
- **Source Collection:** `orders`
- **Array Expansion Path:** `items[]`

| Column | PostgreSQL Type | Source Path | Transform | Nullable |
|---|---|---|---|---|
| `id` | `BIGINT` | `-` | `identity` | False |
| `order_id` | `CHAR(24)` | `_id` | `objectid_hex` | False |
| `position` | `INTEGER` | `$index` | `identity` | False |
| `qty` | `INTEGER` | `items[].qty` | `identity` | False |
| `sku` | `TEXT` | `items[].sku` | `identity` | False |
| `unit_price` | `NUMERIC(12,2)` | `items[].unitPrice` | `decimal_numeric` | False |

### 6. Table `reviews` (root)
- **Source Collection:** `reviews`

| Column | PostgreSQL Type | Source Path | Transform | Nullable |
|---|---|---|---|---|
| `id` | `CHAR(24)` | `_id` | `objectid_hex` | False |
| `body` | `TEXT` | `body` | `identity` | False |
| `created_at` | `TIMESTAMPTZ` | `createdAt` | `date_utc` | False |
| `product_sku` | `TEXT` | `productSku` | `identity` | False |
| `rating` | `SMALLINT` | `rating` | `int_coerce` | False |
| `title` | `TEXT` | `title` | `identity` | False |
| `user_id` | `CHAR(24)` | `userId` | `objectid_hex` | False |

### 7. Table `users_tags` (child)
- **Source Collection:** `users`
- **Array Expansion Path:** `tags[]`

| Column | PostgreSQL Type | Source Path | Transform | Nullable |
|---|---|---|---|---|
| `id` | `BIGINT` | `-` | `identity` | False |
| `user_id` | `CHAR(24)` | `_id` | `objectid_hex` | False |
| `position` | `INTEGER` | `$index` | `identity` | False |
| `value` | `TEXT` | `tags[]` | `identity` | False |
