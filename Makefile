GCP_REGION ?= us-east4

.PHONY: gcp-build
gcp-build:
	gcloud builds submit --region=$(GCP_REGION) --config deploy/gcp/cloudbuild.yaml
