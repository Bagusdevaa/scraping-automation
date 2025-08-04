```
# 1. Tag image untuk GCR
docker tag scraping-automation gcr.io/web-scraping-automation-468004/scraping-automation

# 2. Configure Docker untuk GCR
gcloud auth configure-docker

# 3. Push image ke GCR
docker push gcr.io/web-scraping-automation-468004/scraping-automation
```

```
# Deploy dengan environment variables
gcloud run deploy scraping-automation \
  --image gcr.io/web-scraping-automation-468004/scraping-automation \
  --platform managed \
  --region asia-southeast1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 900s \
  --set-env-vars="DEBUG=false,HEADLESS_MODE=true,SCRAPING_TIMEOUT=60,MAX_RETRIES=5,GOOGLE_SHEET_ID=1I-iGdqCiYwIJuwG-91E1CGTDD6blOkGPr-rJJvtUxBk"
```

```
# Convert credentials ke base64
base64 -i google-credentials.json

# Set sebagai env var di Cloud Run
--set-env-vars="GOOGLE_SHEETS_CREDENTIALS_JSON=<base64_string>"
```

```
# Upload ke Secret Manager
gcloud secrets create google-sheets-credentials --data-file=google-credentials.json

# Deploy dengan secret
gcloud run deploy scraping-automation \
  --set-secrets="GOOGLE_SHEETS_CREDENTIALS_FILE=/secrets/google-credentials:google-sheets-credentials:latest"
```

```
# 1. Tag & Push
docker tag scraping-automation gcr.io/web-scraping-automation-468004/scraping-automation
gcloud auth configure-docker
docker push gcr.io/web-scraping-automation-468004/scraping-automation

# 2. Deploy ke Cloud Run
gcloud run deploy scraping-automation \
  --image gcr.io/web-scraping-automation-468004/scraping-automation \
  --platform managed \
  --region asia-southeast1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 900s \
  --set-env-vars="DEBUG=false,HEADLESS_MODE=true,SCRAPING_TIMEOUT=60,MAX_RETRIES=5,GOOGLE_SHEET_ID=1I-iGdqCiYwIJuwG-91E1CGTDD6blOkGPr-rJJvtUxBk"
```

```
# Weekly automation
gcloud scheduler jobs create http weekly-scraping \
  --schedule="0 9 * * 1" \
  --uri="https://your-service-url/api/v1/scrape/full-workflow-with-sheets?max_properties=100" \
  --http-method=POST
```