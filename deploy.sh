#!/bin/bash

if [[ $1 = "backend" || $1 = "all" ]];
then
    echo "Deploying backend webapp..."
    cd apps/backend
    zip -j backend.zip ../../common/* ./*
    az webapp deployment source config-zip --resource-group aoaivbd1102 --name webApp-Backend-BotId-a3pkv5rdhszks --src "backend.zip"
    cd ../..
fi

if [[ $1 = "frontend" || $1 = "all" ]];
then
    echo "Deploying frontend webapp..."
    cd apps/frontend
    zip frontend.zip ./*
    zip frontend.zip ./pages/*
    zip -j frontend.zip ../../common/*
    az webapp deployment source config-zip --resource-group "aoaivbd1102" --name "webApp-Frontend-a3pkv5rdhszks" --src "frontend.zip"
    cd ../..
fi
