#!/bin/bash
echo "Checking GDPR framework..."
docker-compose exec -T backend python3 << 'PYEOF'
import json

with open('/usr/local/lib/python3.11/site-packages/prowler/compliance/aws/gdpr_aws.json') as f:
    data = json.load(f)
    requirements = data.get('Requirements', [])
    print(f"GDPR: {len(requirements)} controls")
    
    # Show sample
    if requirements:
        first = requirements[0]
        print(f"\nSample control structure:")
        print(f"  Keys: {list(first.keys())}")
        print(f"  ID: {first.get('Id')}")
        print(f"  Name: {first.get('Name', first.get('Description', ''))[:80]}")
        print(f"  Checks: {len(first.get('Checks', []))} Prowler checks mapped")
PYEOF
