#!/usr/bin/env bash
set -euo pipefail

# Generate today’s date suffix
today=$(date +%Y_%m_%d)
out_file="bucket_size_${today}.csv"

# Write CSV header
printf "Region,Size(GB)\n" > "${out_file}"

for region in br ca eu il us; do # This should be extended if we add more regions
  bucket="sp-assets-${region}"

  # 1) List every object, recursively, then summarize
  raw_summary=$(aws s3 ls "s3://${bucket}" \
                  --recursive \
                  --summarize)

  # 2) Extract the "Total Size" value (in bytes)
  total_bytes=$(awk '/Total Size:/ { print $3 }' <<< "$raw_summary")

  # 3) Convert bytes → GB with 2 decimals
  size_gb=$(awk -v b="$total_bytes" 'BEGIN { printf("%.2f", b/(1024^3)) }')

  # 4) Append a CSV row
  printf "%s,%s\n" "${region}" "${size_gb}" >> "${out_file}"
done

echo "Written bucket sizes to ${out_file}"

# 5) Copy report to Google Drive using rclone
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