#!/usr/bin/env bash
# Run in Google Cloud Shell as the owner/admin of this project.
# Creates keyless trust for this repository's main Japanese workflow only.
set -euo pipefail

tts_project='project-3558f1ce-afb8-4e93-8b2'
tts_account='jp-tts@project-3558f1ce-afb8-4e93-8b2.iam.gserviceaccount.com'
tts_pool='github-japanese-tts'
tts_provider='daily-japanese'
tts_repo_id='1177202395'
tts_owner_id='266441586'
tts_workflow='Gracieme/agent-for-news/.github/workflows/japanese-daily.yml@refs/heads/main'
tts_mapping='google.subject=assertion.sub,attribute.repository_id=assertion.repository_id,attribute.repository_owner_id=assertion.repository_owner_id,attribute.ref=assertion.ref,attribute.workflow_ref=assertion.workflow_ref'
tts_condition="assertion.repository_id == '${tts_repo_id}' && assertion.repository_owner_id == '${tts_owner_id}' && assertion.ref == 'refs/heads/main' && assertion.workflow_ref == '${tts_workflow}'"

printf '%s\n' "Project: ${tts_project}" "Service account: ${tts_account}" \
  'This setup enables Cloud TTS and creates short-lived GitHub OIDC trust.' \
  'It does not create JSON keys or change organization policies.'
gcloud iam service-accounts describe "${tts_account}" --project="${tts_project}" --format='value(email)'
tts_number=$(gcloud projects describe "${tts_project}" --format='value(projectNumber)')
if [[ ! "${tts_number}" =~ ^[0-9]+$ ]]; then
  printf '%s\n' 'Could not determine project number.' >&2
  exit 1
fi

gcloud services enable iam.googleapis.com iamcredentials.googleapis.com sts.googleapis.com \
  texttospeech.googleapis.com --project="${tts_project}"

if ! gcloud iam workload-identity-pools describe "${tts_pool}" --location=global \
  --project="${tts_project}" --format='value(name)' >/dev/null 2>&1; then
  gcloud iam workload-identity-pools create "${tts_pool}" --location=global \
    --project="${tts_project}" --display-name='Japanese daily GitHub workflow'
fi

# Keep this dedicated pool exclusive to this one provider. A second, broader
# provider in the same pool could otherwise satisfy an attribute IAM binding.
tts_other_providers=$(gcloud iam workload-identity-pools providers list \
  --workload-identity-pool="${tts_pool}" --location=global --project="${tts_project}" \
  --format='value(name)' | while IFS= read -r name; do
    [[ -z "${name}" || "${name##*/}" == "${tts_provider}" ]] || printf '%s\n' "${name}"
  done)
if [[ -n "${tts_other_providers}" ]]; then
  printf '%s\n' 'This pool has other providers. Stop and ask for a dedicated pool review.' >&2
  exit 1
fi

if gcloud iam workload-identity-pools providers describe "${tts_provider}" --location=global \
  --workload-identity-pool="${tts_pool}" --project="${tts_project}" --format=json >/dev/null 2>&1; then
  # Validate an existing configuration; do not silently broaden or replace it.
  gcloud iam workload-identity-pools providers describe "${tts_provider}" --location=global \
    --workload-identity-pool="${tts_pool}" --project="${tts_project}" --format=json | \
    python3 -c 'import json,sys; d=json.load(sys.stdin); expected=dict(p.split("=",1) for p in sys.argv[2].split(",")); ok=d.get("attributeCondition")==sys.argv[1] and d.get("attributeMapping")==expected and d.get("oidc",{}).get("issuerUri")=="https://token.actions.githubusercontent.com" and not d.get("disabled",False); sys.exit(0 if ok else "Existing provider differs; stop and review its trust configuration.")' \
      "${tts_condition}" "${tts_mapping}"
else
  gcloud iam workload-identity-pools providers create-oidc "${tts_provider}" \
    --project="${tts_project}" --location=global --workload-identity-pool="${tts_pool}" \
    --display-name='Main Japanese daily workflow only' \
    --issuer-uri='https://token.actions.githubusercontent.com' \
    --attribute-mapping="${tts_mapping}" --attribute-condition="${tts_condition}"
fi

tts_member="principalSet://iam.googleapis.com/projects/${tts_number}/locations/global/workloadIdentityPools/${tts_pool}/attribute.repository_id/${tts_repo_id}"
gcloud iam service-accounts add-iam-policy-binding "${tts_account}" --project="${tts_project}" \
  --role='roles/iam.workloadIdentityUser' --member="${tts_member}" --condition=None
gcloud projects add-iam-policy-binding "${tts_project}" \
  --role='roles/serviceusage.serviceUsageConsumer' --member="serviceAccount:${tts_account}" --condition=None

printf '\n%s\n' 'SETUP COMPLETE — send the following non-secret values back to Codex:'
printf 'GOOGLE_CLOUD_PROJECT=%s\n' "${tts_project}"
printf 'GOOGLE_CLOUD_SERVICE_ACCOUNT=%s\n' "${tts_account}"
printf 'GOOGLE_CLOUD_WIF_PROVIDER=projects/%s/locations/global/workloadIdentityPools/%s/providers/%s\n' \
  "${tts_number}" "${tts_pool}" "${tts_provider}"
printf '%s\n' 'Google IAM changes can take several minutes to propagate.'
