#!/bin/sh
cd kmp/
#git stash
#git pull origin dev
#git stash pop
npm install
npm run build
cp ./src/index.html ./../flask_backend/templates/
cp ./dist/bundle.* ./../flask_backend/static/
cp -r ./dist/static/images/ ./../flask_backend/static/
cp -r ./dist/static/fonts/ ./../flask_backend/static/
echo "Successfully Finished building UI"
