#!/bin/bash

if [ ! -d "./env" ]; then 
    echo "Creating venv"
    python3 -m venv env
fi

echo "Upgrade pip"
./env/bin/pip install pip --upgrade

echo "Install requirements.txt"
./env/bin/pip install -r requirements.txt
