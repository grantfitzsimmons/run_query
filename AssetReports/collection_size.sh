#!/usr/bin/env bash
set -euo pipefail

# Map your bucket suffix → AWS region
declare -A aws_region=(
  [br]=sa-east-1
  [ca]=ca-central-1
  [eu]=eu-west-1
  [il]=il-central-1
  [us]=us-east-1
)

# Generate date suffix and output file
today=$(date +%Y_%m_%d)
out_file="collection_size_${today}.csv"

# Write CSV header
printf "Region,Instance,Size(GB)\n" > "${out_file}"

for suffix in br ca eu il us; do
  bucket="sp-assets-${suffix}"
  region="${aws_region[$suffix]}"

  # 1) List objects + sizes in correct region
  aws s3api list-objects-v2 \
    --bucket "${bucket}" \
    --query 'Contents[].[Key,Size]' \
    --output text \
    --region "${region}" \
  | \
  # 2) Group by first‐level prefix (instance)
  awk '
    {
      split($1, parts, "/")
      inst = parts[1]
      sum[inst] += $2
    }
    END {
      for (i in sum) {
        printf("%s,%d\n", i, sum[i])
      }
    }
  ' \
  | \
  sort \
  | \
  # 3) Convert to GB, format CSV rows
  while IFS=',' read -r inst total_bytes; do
    size_gb=$(awk -v b="$total_bytes" 'BEGIN{ printf("%.2f", b/(1024^3)) }')
    printf "%s,%s,%s\n" "${suffix}" "${inst}" "${size_gb}"
  done >> "${out_file}"
done

echo "Written collection sizes to ${out_file}"

# 4) Copy report to Google Drive via rclone
echo "Copying ${out_file} to Google Drive..."
rclone copy \
  "${out_file}" \
  "sccvault:Member Files/Asset Reports/" \
  --progress \
  --transfers=8 \
  --checkers=16 \
  --drive-chunk-size=64M \
  --drive-upload-cutoff=64M

echo "Report uploaded successfully!"