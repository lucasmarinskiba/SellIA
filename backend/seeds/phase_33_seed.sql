-- Phase 33 Seed Data - SQL Insert
-- Real numbers for multi-platform seller automation

-- Products
INSERT INTO products (id, seller_id, sku, title, description, category, cost, price_base, images, brand, stock_total, stock_reserved, is_digital, created_at, updated_at)
VALUES
  ('550e8400-e29b-41d4-a716-446655440001'::uuid, 'seller-sellbot-001', 'HDP-PRO-001', 'Premium Wireless Headphones Pro', 'High-quality wireless headphones with noise cancellation', 'Audio', 45.0, 99.99, ARRAY['img1.jpg', 'img2.jpg'], 'AudioPro', 250, 45, false, NOW() - INTERVAL '60 days', NOW()),
  ('550e8400-e29b-41d4-a716-446655440002'::uuid, 'seller-sellbot-001', 'CHG-FAST-002', 'Fast Wireless Charging Pad', '15W wireless charging pad for phones', 'Accessories', 18.0, 49.99, ARRAY['img1.jpg'], 'ChargePro', 500, 120, false, NOW() - INTERVAL '45 days', NOW()),
  ('550e8400-e29b-41d4-a716-446655440003'::uuid, 'seller-sellbot-001', 'USB-CABLE-003', 'USB-C Fast Data Cable', 'Premium USB-C cable for fast charging and data transfer', 'Cables', 3.0, 12.99, ARRAY['img1.jpg'], 'DataLink', 2000, 300, false, NOW() - INTERVAL '30 days', NOW()),
  ('550e8400-e29b-41d4-a716-446655440004'::uuid, 'seller-sellbot-001', 'COURSE-AI-001', 'Complete AI Automation Masterclass', 'Learn AI automation with Python and GPT APIs', 'Courses', 5.0, 99.99, ARRAY[]::text[], 'SellIA Academy', 500, 0, true, NOW() - INTERVAL '15 days', NOW());

-- Platform Listings
INSERT INTO platform_listings (id, product_id, platform, platform_sku, listing_url, status, current_stock, current_price, rating, rating_count, sales_this_month, best_seller_rank, last_sync_at, created_at, updated_at)
VALUES
  ('660e8400-e29b-41d4-a716-446655440001'::uuid, '550e8400-e29b-41d4-a716-446655440001'::uuid, 'mercado_libre', 'MLA-12345678', 'https://mercado_libre.com/MLA-12345678', 'active', 250, 99.99, 8.2, 64, 425, 1, NOW(), NOW(), NOW()),
  ('660e8400-e29b-41d4-a716-446655440002'::uuid, '550e8400-e29b-41d4-a716-446655440001'::uuid, 'amazon', 'B09X1Y2Z3A', 'https://amazon.com/B09X1Y2Z3A', 'active', 250, 99.99, 8.0, 52, 380, 1, NOW(), NOW(), NOW()),
  ('660e8400-e29b-41d4-a716-446655440003'::uuid, '550e8400-e29b-41d4-a716-446655440001'::uuid, 'hotmart', 'HM-12345678', 'https://hotmart.com/HM-12345678', 'active', 250, 99.99, 8.4, 38, 250, 1, NOW(), NOW(), NOW()),
  ('660e8400-e29b-41d4-a716-446655440004'::uuid, '550e8400-e29b-41d4-a716-446655440002'::uuid, 'mercado_libre', 'MLA-87654321', 'https://mercado_libre.com/MLA-87654321', 'active', 500, 49.99, 7.8, 45, 310, 3, NOW(), NOW(), NOW()),
  ('660e8400-e29b-41d4-a716-446655440005'::uuid, '550e8400-e29b-41d4-a716-446655440002'::uuid, 'amazon', 'B09X2Y3Z4B', 'https://amazon.com/B09X2Y3Z4B', 'active', 500, 49.99, 7.6, 38, 280, 3, NOW(), NOW(), NOW()),
  ('660e8400-e29b-41d4-a716-446655440006'::uuid, '550e8400-e29b-41d4-a716-446655440002'::uuid, 'hotmart', 'HM-87654321', 'https://hotmart.com/HM-87654321', 'active', 500, 49.99, 8.1, 28, 180, 1, NOW(), NOW(), NOW()),
  ('660e8400-e29b-41d4-a716-446655440007'::uuid, '550e8400-e29b-41d4-a716-446655440003'::uuid, 'mercado_libre', 'MLA-11223344', 'https://mercado_libre.com/MLA-11223344', 'active', 2000, 12.99, 7.5, 68, 1200, 1, NOW(), NOW(), NOW()),
  ('660e8400-e29b-41d4-a716-446655440008'::uuid, '550e8400-e29b-41d4-a716-446655440003'::uuid, 'amazon', 'B09X3Y4Z5C', 'https://amazon.com/B09X3Y4Z5C', 'active', 2000, 12.99, 7.4, 55, 950, 2, NOW(), NOW(), NOW()),
  ('660e8400-e29b-41d4-a716-446655440009'::uuid, '550e8400-e29b-41d4-a716-446655440004'::uuid, 'hotmart', 'HM-11223344', 'https://hotmart.com/HM-11223344', 'active', 500, 99.99, 9.2, 85, 350, 1, NOW(), NOW(), NOW());

-- Seller Metrics
INSERT INTO seller_metrics (id, seller_id, platform, metric_date, active_listings, bestseller_count, top_5_count, avg_rating, total_reviews, daily_orders, daily_gmv, conversion_rate, return_rate)
VALUES
  ('770e8400-e29b-41d4-a716-446655440001'::uuid, 'seller-sellbot-001', 'mercado_libre', CURRENT_DATE, 150, 8, 25, 4.8, 500, 50, 8000.0, 0.12, 0.02),
  ('770e8400-e29b-41d4-a716-446655440002'::uuid, 'seller-sellbot-001', 'amazon', CURRENT_DATE, 120, 3, 15, 4.7, 400, 40, 6000.0, 0.10, 0.02),
  ('770e8400-e29b-41d4-a716-446655440003'::uuid, 'seller-sellbot-001', 'hotmart', CURRENT_DATE, 80, 1, 5, 4.9, 200, 30, 4000.0, 0.15, 0.02);

-- Print confirmation
SELECT COUNT(*) as products_inserted FROM products;
SELECT COUNT(*) as listings_inserted FROM platform_listings;
SELECT COUNT(*) as metrics_inserted FROM seller_metrics;
