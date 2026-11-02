#!/bin/bash

echo "=== Extracting Prowler Compliance Framework Mappings ==="
echo ""

echo "1. ISO 27001 Framework Structure:"
docker-compose exec -T backend bash -c "cat /usr/local/lib/python3.11/site-packages/prowler/compliance/aws/iso27001_2013_aws.json | python3 -m json.tool | head -100"
echo ""

echo "2. NIST CSF Framework Structure:"
docker-compose exec -T backend bash -c "cat /usr/local/lib/python3.11/site-packages/prowler/compliance/aws/nist_csf_1.1_aws.json | python3 -m json.tool | head -100"
echo ""

echo "3. Count controls per framework:"
docker-compose exec -T backend python3 << 'PYEOF'
import json

frameworks = {
    'ISO 27001': '/usr/local/lib/python3.11/site-packages/prowler/compliance/aws/iso27001_2013_aws.json',
    'NIST CSF': '/usr/local/lib/python3.11/site-packages/prowler/compliance/aws/nist_csf_1.1_aws.json',
    'PCI-DSS': '/usr/local/lib/python3.11/site-packages/prowler/compliance/aws/pci_3.2.1_aws.json',
    'CIS AWS': '/usr/local/lib/python3.11/site-packages/prowler/compliance/aws/cis_2.0_aws.json'
}

for name, path in frameworks.items():
    with open(path) as f:
        data = json.load(f)
        # Try different possible structures
        if 'Requirements' in data:
            controls = data['Requirements']
        elif 'Controls' in data:
            controls = data['Controls']
        else:
            controls = data
        
        total_controls = len(controls) if isinstance(controls, list) else len(controls.keys())
        print(f"{name}: {total_controls} controls")
        
        # Show first control structure
        if isinstance(controls, list):
            first = controls[0]
        else:
            first = list(controls.values())[0]
        
        print(f"  Sample keys: {list(first.keys())[:5]}")
        print()
PYEOF
