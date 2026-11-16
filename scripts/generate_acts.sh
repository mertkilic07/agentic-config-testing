#!/usr/bin/env bash
# Generate the 2-way covering array from the ACTS model.
# Usage (inside the container): bash scripts/generate_acts.sh
set -euo pipefail
cd "$(dirname "$0")/.."
java -Djava.awt.headless=true \
     -Ddoi=2 \
     -Doutput=csv \
     -Dcheck=on \
     -jar /opt/acts/acts.jar \
     models/sqlite-acts.txt \
     configs/sqlite-pairwise.csv
echo "Written: configs/sqlite-pairwise.csv"
