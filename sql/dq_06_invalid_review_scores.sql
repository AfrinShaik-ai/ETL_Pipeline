
SELECT COUNT(*) AS failed_rows
FROM stg_reviews
WHERE review_score IS NULL
   OR review_score NOT BETWEEN 1 AND 5;
