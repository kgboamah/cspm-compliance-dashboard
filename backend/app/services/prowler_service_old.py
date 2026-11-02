import subprocess
import json
import tempfile
import os
from typing import Dict, List, Any


class ProwlerService:
    def run_scan(self, cloud_provider: str, access_key: str, secret_key: str, regions: List[str], account_id: str) -> Dict[str, Any]:
        """Execute Prowler 3.x scan with environment variables for credentials"""
        try:
            output_dir = '/tmp/prowler-output'
            os.makedirs(output_dir, exist_ok=True)

            # Set AWS credentials as environment variables (Prowler 3.x preferred method)
            env = os.environ.copy()
            env['AWS_ACCESS_KEY_ID'] = access_key
            env['AWS_SECRET_ACCESS_KEY'] = secret_key
            
            # Set default region if specified
            if regions:
                env['AWS_DEFAULT_REGION'] = regions[0]

            # Build Prowler 3.x command with CORRECT syntax
            cmd = [
                'prowler',
                'aws',
                '-M', 'json',  # Output mode (not --output-formats)
                '-F', 'prowler-output',  # Output filename (not --output-filename)
                '-o', output_dir,  # Output directory (not --output-directory)
                '-q'  # Quiet mode (no banner)
            ]

            # Add region filter if specified
            if regions:
                for region in regions:
                    cmd.extend(['-f', region])

            print(f"[Prowler] Starting scan for account {account_id}")
            print(f"[Prowler] Command: {' '.join(cmd[:7])}... (credentials via env)")
            print(f"[Prowler] Regions: {regions}")

            # Run Prowler with 30-minute timeout
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=1800,
                env=env
            )

            print(f"[Prowler] Return code: {result.returncode}")
            
            # Prowler exit codes: 0 = all pass, 3 = some checks failed (normal), other = error
            if result.returncode not in [0, 3]:
                print(f"[Prowler] STDOUT: {result.stdout[:500]}")
                print(f"[Prowler] STDERR: {result.stderr[:500]}")
                return {'success': False, 'error': result.stderr, 'findings': []}

            # Parse Prowler output (JSON format, one finding per line - JSONL)
            findings = []
            output_file = os.path.join(output_dir, 'prowler-output.json')
            
            try:
                if os.path.exists(output_file):
                    print(f"[Prowler] Reading output from {output_file}")
                    with open(output_file, 'r') as f:
                        # Prowler 3.x outputs a single JSON array containing all findings
                        data = json.load(f)
                        
                        # data should be a list of finding objects
                        if isinstance(data, list):
                            for finding in data:
                                findings.append(self._parse_prowler_finding(finding))
                        else:
                            print(f"[Prowler] Warning: Expected JSON array, got {type(data)}")
                            
                else:
                    print(f"[Prowler] Warning: Output file not found at {output_file}")
                    print(f"[Prowler] Files in {output_dir}: {os.listdir(output_dir) if os.path.exists(output_dir) else 'directory does not exist'}")
                        
            except Exception as e:
                print(f"[Prowler] Error parsing output: {e}")
                import traceback
                traceback.print_exc()

            print(f"[Prowler] Scan completed. {len(findings)} findings.")
            return {'success': True, 'findings': findings}

        except subprocess.TimeoutExpired:
            print("[Prowler] Scan timeout after 30 minutes")
            return {'success': False, 'error': 'Scan timeout after 30 minutes', 'findings': []}
        except Exception as e:
            print(f"[Prowler] Exception: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e), 'findings': []}

    def _parse_prowler_finding(self, finding: Dict[str, Any]) -> Dict[str, Any]:
        """Parse a Prowler 3.x finding object into our standard format"""
        return {
            'check_id': finding.get('CheckID', 'unknown'),
            'check_title': finding.get('CheckTitle', ''),
            'service_name': finding.get('ServiceName', ''),
            'resource_id': finding.get('ResourceDetails', '')[:255] if finding.get('ResourceDetails') else '',
            'resource_type': finding.get('ResourceType', '')[:100] if finding.get('ResourceType') else '',
            'status': finding.get('Status', 'UNKNOWN').upper(),  # PASS, FAIL, etc.
            'status_extended': finding.get('StatusExtended', ''),
            'severity': finding.get('Severity', 'informational').lower(),  # critical, high, medium, low
            'region': finding.get('Region', ''),
            'compliance': finding.get('Compliance', {}),
            'raw_data': finding
        }

    def _parse_prowler_finding(self, finding: dict) -> dict:
        """Parse a single Prowler finding into our format"""
        return {
            'check_id': finding.get('CheckID', finding.get('Id', 'unknown')),
            'check_title': finding.get('CheckTitle', finding.get('Title', '')),
            'service_name': finding.get('ServiceName', finding.get('Service', '')),
            'resource_id': finding.get('ResourceId', finding.get('Resource', '')),
            'resource_type': finding.get('ResourceType', finding.get('ResourceType', '')),
            'status': finding.get('Status', finding.get('Compliance', {}).get('Status', 'UNKNOWN')),
            'status_extended': finding.get('StatusExtended', finding.get('Description', '')),
            'severity': finding.get('Severity', finding.get('Severity', {}).get('Label', 'INFORMATIONAL')).lower(),
            'region': finding.get('Region', ''),
            'compliance': finding.get('Compliance', {}),
            'raw_data': finding
        }

    def get_check_catalog(self) -> Dict[str, Any]:
        """Get available Prowler checks"""
        try:
            # Run prowler to list checks
            result = subprocess.run(
                ['prowler', 'aws', '--list-checks'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'checks': result.stdout.split('\n')
                }
            else:
                return {
                    'success': False,
                    'message': 'Could not retrieve check catalog'
                }
        except Exception as e:
            return {
                'success': False,
                'message': str(e)
            }