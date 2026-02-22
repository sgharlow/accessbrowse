#!/bin/bash
# deploy.sh — Deploy AccessBrowse to Cloud Run
set -e

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-accessbrowse-hackathon}"
REGION="us-central1"
SERVICE="accessbrowse"

echo "Deploying AccessBrowse to Cloud Run..."
echo "  Project: $PROJECT_ID"
echo "  Region:  $REGION"
echo "  Service: $SERVICE"

# Build and deploy
gcloud run deploy $SERVICE \
    --source ./backend \
    --project $PROJECT_ID \
    --region $REGION \
    --allow-unauthenticated \
    --memory 1Gi \
    --timeout 300 \
    --set-env-vars "GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GOOGLE_CLOUD_LOCATION=$REGION"

# Print service URL
echo ""
echo "Service URL:"
gcloud run services describe $SERVICE \
    --project $PROJECT_ID \
    --region $REGION \
    --format "value(status.url)"
