docker build -t defillama-scraper .
docker tag defillama-scraper jasong03/defillama-scraper:latest
docker push jasong03/defillama-scraper:latest