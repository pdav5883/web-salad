rm lambda.zip
zip lambda.zip lambda_function.py
aws lambda update-function-code --function-name SaladQueryGame --zip-file fileb:///home/peter/Projects/web-salad/lambdas/query_game/lambda.zip
