#!/bin/bash
python3 /var/www/html/LiveActionMap/scrape.py
mv /var/www/html/index.html mv /var/www/html/history/"$(date +"%H-%M-%m-%d-%Y")$".html
mv /var/www/html/LiveActionMap/dist/index.html /var/www/html/index.html
mv /var/www/html/LiveActionMap/dist/overlay.css /var/www/html/overlay.css
