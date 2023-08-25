# package layer
rm common.zip
mkdir -p _tmp/python/common
cp *.py _tmp/python/common
cd _tmp
zip -r common.zip python
mv common.zip ..
cd ..
rm -rf _tmp

# update layer in AWS
aws lambda publish-layer-version \
    --layer-name web-salad-common \
    --zip-file fileb:///home/peter/Projects/web-salad/lambdas/common/common.zip \
    --description "$1" \
    --compatible-runtimes python3.8

version=$(aws lambda list-layer-versions --layer-name web-salad-common | python3 -c "import sys, json; print(json.load(sys.stdin)['LayerVersions'][0]['LayerVersionArn'])")

# update lambdas to use new layer
aws lambda update-function-configuration --function-name SaladQueryGame --layers $version
