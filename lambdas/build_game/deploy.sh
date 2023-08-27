rm lambda.zip
zip lambda.zip lambda_function.py
aws lambda update-function-code --function-name SaladBuildGame --zip-file fileb:///home/peter/Projects/web-salad/lambdas/build_game/lambda.zip
