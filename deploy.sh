#!/bin/bash

# Defaults for variables the script will prompt for
DEFAULT_GCP_PROJECT=$(gcloud config get-value project)

# Defaults for variables the script won't prompt for
JOB_NAME="coinbase-ynab-sync"

# Prompt for the GCP project ID
read -p "Enter the GCP_PROJECT (default: $DEFAULT_GCP_PROJECT): " GCP_PROJECT
if [[ -z "$GCP_PROJECT" ]]; then
  GCP_PROJECT="$DEFAULT_GCP_PROJECT"
fi

# Deploy the Cloud Run job
echo "Deploying Cloud Run job: $JOB_NAME"
gcloud run jobs deploy "$JOB_NAME" --source=. --project="$GCP_PROJECT"
