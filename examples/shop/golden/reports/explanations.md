# Database Similarity Analysis

Overall database schema similarity is 93.5%.
Classification: MATCHED.
Top 7 fields affecting alignment:
- userId -> orders.user_id (score: 75.5%, reasons: )
- userId -> reviews.user_id (score: 75.5%, reasons: )
- tags[] -> users_tags.value (score: 78.3%, reasons: )
- rating -> reviews.rating (score: 80.0%, reasons: TYPE_PURITY_LOW)
- categories[] -> products_categories.value (score: 80.0%, reasons: )
