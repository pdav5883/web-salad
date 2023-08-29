rm lambda.zip
zip lambda.zip lambda_function.py
aws lambda update-function-code --function-name SaladPlayGame --zip-file fileb:///home/peter/Projects/web-salad/lambdas/play_game/lambda.zip
