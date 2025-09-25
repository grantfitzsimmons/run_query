#!/usr/bin/env bash
set -euo pipefail

# Generate today’s date suffix
today=$(date +%Y_%m_%d)
out_file="collection_size_${today}.csv"

# Write CSV header
printf "Region,Instance,Size(GB)\n" > "${out_file}"

for region in br ca eu il us; do # This should be extended if we add more regions
  bucket="sp-assets-${region}"

  # List objects and sizes, group by top-level prefix, sort, and emit CSV lines
  aws s3api list-objects-v2 \
    --bucket "${bucket}" \
    --query 'Contents[].[Key,Size]' \
    --output text \
  | \
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
  | sort \
  | while IFS=',' read -r inst total_bytes; do
      # Convert bytes to GB with 2 decimals
      size_gb=$(awk -v b="$total_bytes" 'BEGIN{ printf("%.2f", b/(1024^3)) }')
      printf "%s,%s,%s\n" "${region}" "${inst}" "${size_gb}"
    done >> "${out_file}"
done

echo "Written collection sizes to ${out_file}"

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