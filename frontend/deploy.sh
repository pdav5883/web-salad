aws s3 sync . s3://budget-tracker-public --exclude="*" --include="*.html" --include="*.css" --include="*.js"
aws cloudfront create-invalidation --distribution-id E12ROA9K04TP3O --paths "/*"
