aws s3 sync . s3://web-salad-public --exclude="*" --include="*.html" --include="*.css" --include="*.js"
aws cloudfront create-invalidation --distribution-id E1IY0UIOIH9K5C --paths "/*"
