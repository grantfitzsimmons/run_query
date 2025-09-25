#!/usr/bin/env bash
set -euo pipefail

# Map your bucket suffix → actual AWS region
declare -A aws_region=(
  [br]=sa-east-1      # sp-assets-br
  [ca]=ca-central-1   # sp-assets-ca
  [eu]=eu-west-1      # sp-assets-eu
  [il]=il-central-1   # sp-assets-il
  [us]=us-east-1      # sp-assets-us
)

# Date for filename
today=$(date +%Y_%m_%d)
out_file="bucket_size_${today}.csv"

# CSV header
printf "Region,Size(GB)\n" > "${out_file}"

for suffix in br ca eu il us; do
  bucket="sp-assets-${suffix}"
  region="${aws_region[$suffix]}"

  # List objects in the correct region
  raw=$(aws s3 ls "s3://${bucket}" \
          --recursive \
          --summarize \
          --region "${region}")

  # Extract total bytes
  bytes=$(awk '/Total Size:/ {print $3}' <<< "$raw")

  # Convert to GB (2 decimals)
  gb=$(awk -v b="$bytes" 'BEGIN{ printf("%.2f", b/(1024^3)) }')

  # Append CSV row
  printf "%s,%s\n" "${suffix}" "${gb}" >> "${out_file}"
done

echo "Written bucket sizes to ${out_file}"

echo "Uploading report to Google Drive…"
rclone copy \
  "${out_file}" \
  "sccvault:Member Files/Asset Reports/" \
  --progress \
  --transfers=8 \
  --checkers=16 \
  --drive-chunk-size=64M \
  --drive-upload-cutoff=64M

echo "Done."