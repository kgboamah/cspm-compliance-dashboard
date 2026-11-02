#!/bin/bash

echo "=== Exploring Prowler Compliance Metadata ==="
echo ""

echo "1. Contents of compliance directory:"
docker-compose exec -T backend bash -c "ls -la /usr/local/lib/python3.11/site-packages/prowler/compliance/"
echo ""

echo "2. Compliance framework files:"
docker-compose exec -T backend bash -c "find /usr/local/lib/python3.11/site-packages/prowler/compliance -name '*.json' -o -name '*.yaml' | head -20"
echo ""

echo "3. Sample metadata file (accessanalyzer_enabled):"
docker-compose exec -T backend bash -c "cat /usr/local/lib/python3.11/site-packages/prowler/providers/aws/services/accessanalyzer/accessanalyzer_enabled/accessanalyzer_enabled.metadata.json 2>/dev/null"
echo ""

echo "4. Count total metadata files:"
docker-compose exec -T backend bash -c "find /usr/local/lib/python3.11/site-packages/prowler/providers/aws -name '*.metadata.json' | wc -l"
echo ""

echo "5. Sample: First 3 metadata files with compliance info:"
docker-compose exec -T backend python3 << 'PYEOF'
import json
from pathlib import Path

prowler_path = Path("/usr/local/lib/python3.11/site-packages/prowler")
metadata_files = list(prowler_path.rglob("*.metadata.json"))

print(f"Total metadata files found: {len(metadata_files)}\n")

for i, mfile in enumerate(metadata_files[:3]):
    print(f"--- File {i+1}: {mfile.name} ---")
    with open(mfile) as f:
        data = json.load(f)
        # Show compliance-related fields
        if "Compliance" in data:
            print(f"Compliance: {json.dumps(data['Compliance'], indent=2)}")
        else:
            print(f"Keys in metadata: {list(data.keys())}")
    print()
PYEOF
