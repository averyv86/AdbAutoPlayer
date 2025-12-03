#!/usr/bin/env python3
"""
Agent 21: Kernel Extension Memory Analyzer
Analyzes kernel extension (kext) memory usage and identifies safe unload candidates
Part of macOS Resource Optimizer v2.0 - System Optimization Week 5
"""

import json
import sys
import subprocess
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple


class KextAnalyzer:
    """
    Analyzes kernel extensions for memory usage and safety
    """

    # System-critical kext patterns that must NEVER be unloaded
    CRITICAL_KEXT_PATTERNS = [
        # Kernel Programming Interfaces (180+ patterns)
        r'^com\.apple\.kpi\..*',
        r'^com\.apple\.security\..*',
        r'^com\.apple\.iokit\..*',

        # Critical system drivers
        r'^com\.apple\.driver\.AppleACPIPlatform$',
        r'^com\.apple\.driver\.AppleAPIC$',
        r'^com\.apple\.driver\.AppleSMC$',
        r'^com\.apple\.driver\.AppleRTC$',
        r'^com\.apple\.driver\.AppleHPET$',
        r'^com\.apple\.driver\.AppleIntelCPUPowerManagement$',
        r'^com\.apple\.driver\.AppleACPICPU$',
        r'^com\.apple\.driver\.AppleEFI.*',
        r'^com\.apple\.driver\.AppleFDEKeyStore$',
        r'^com\.apple\.driver\.AppleKeyStore$',

        # Storage and filesystem
        r'^com\.apple\.driver\.AppleAHCI.*',
        r'^com\.apple\.driver\.AppleNVMe.*',
        r'^com\.apple\.iokit\.IOAHCIFamily$',
        r'^com\.apple\.iokit\.IOStorageFamily$',
        r'^com\.apple\.iokit\.IONVMeFamily$',
        r'^com\.apple\.filesystems\..*',

        # Network stack (critical)
        r'^com\.apple\.iokit\.IONetworkingFamily$',
        r'^com\.apple\.driver\.networking\..*',
        r'^com\.apple\.nke\..*',

        # USB and peripherals (critical)
        r'^com\.apple\.iokit\.IOUSBFamily$',
        r'^com\.apple\.iokit\.IOUSBHostFamily$',
        r'^com\.apple\.driver\.usb\..*',
        r'^com\.apple\.driver\.AppleUSB.*',

        # Graphics (critical for display)
        r'^com\.apple\.iokit\.IOGraphicsFamily$',
        r'^com\.apple\.driver\.AppleGraphics.*',
        r'^com\.apple\.driver\.AppleIntelFramebuffer.*',
        r'^com\.apple\.AppleGPU.*',

        # Audio
        r'^com\.apple\.iokit\.IOAudioFamily$',
        r'^com\.apple\.driver\.AppleHDA$',
        r'^com\.apple\.audio\..*',

        # Power management
        r'^com\.apple\.driver\.AppleIntelPowerManagement$',
        r'^com\.apple\.driver\.AppleUpstreamUserClient$',
        r'^com\.apple\.driver\.pmtelemetry$',

        # Bluetooth and wireless
        r'^com\.apple\.iokit\.IOBluetoothFamily$',
        r'^com\.apple\.iokit\.IO80211Family$',

        # HID devices (keyboard, mouse, trackpad)
        r'^com\.apple\.iokit\.IOHIDFamily$',
        r'^com\.apple\.driver\.AppleHID.*',
        r'^com\.apple\.driver\.AppleMultitouch.*',
        r'^com\.apple\.driver\.AppleTopCase.*',

        # Thunderbolt
        r'^com\.apple\.driver\.AppleThunderbolt.*',
        r'^com\.apple\.iokit\.IOThunderboltFamily$',

        # Platform support
        r'^com\.apple\.iokit\.IOPlatformPluginFamily$',
        r'^com\.apple\.driver\.X86PlatformPlugin$',

        # System services
        r'^com\.apple\.driver\.AppleBCM.*',
        r'^com\.apple\.driver\.DiskImages$',
        r'^com\.apple\.driver\.CoreStorage$',
        r'^com\.apple\.driver\.AppleFSCompressionTypeDataless$',
    ]

    # Additional protected patterns (hardware-specific)
    PROTECTED_HARDWARE_PATTERNS = [
        r'^com\.apple\.driver\.AppleIntel.*',
        r'^com\.apple\.driver\.AppleAMD.*',
        r'^com\.apple\.driver\.AppleNVIDIA.*',
        r'^com\.apple\.driver\.AppleSSD.*',
        r'^com\.apple\.driver\.AppleT2.*',
        r'^com\.apple\.driver\.AppleM1.*',
        r'^com\.apple\.driver\.AppleM2.*',
    ]

    def __init__(self, config_path: Path = None):
        """Initialize kernel extension analyzer"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / 'config' / 'cleanup-rules.json'

        self.config = self._load_config(config_path)

        # Memory thresholds (in MB)
        self.memory_thresholds = {
            'small': 1,      # <1 MB (normal)
            'medium': 5,     # 1-5 MB (normal)
            'large': 50,     # 5-50 MB (caution)
            'abnormal': 50   # >50 MB (investigate)
        }

    def _load_config(self, config_path: Path) -> dict:
        """Load kext analysis configuration"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                return config.get('kernel_extension_analysis', {
                    'enabled': True,
                    'memory_threshold_mb': 50,
                    'exclude_critical': True
                })
        except Exception as e:
            print(f"Warning: Could not load config: {e}")
            return {
                'enabled': True,
                'memory_threshold_mb': 50,
                'exclude_critical': True
            }

    def enumerate_kernel_extensions(self) -> List[Dict]:
        """
        Enumerate all loaded kernel extensions via kextstat

        Returns:
            List of kext dictionaries with index, refs, size, wired, bundle_id
        """
        try:
            result = subprocess.run(
                ['kextstat'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                print(f"Error running kextstat: {result.stderr}")
                return []

            kexts = []
            lines = result.stdout.strip().split('\n')

            # Skip header line
            for line in lines[1:]:
                kext = self._parse_kextstat_line(line)
                if kext:
                    kexts.append(kext)

            return kexts

        except subprocess.TimeoutExpired:
            print("Error: kextstat command timed out")
            return []
        except Exception as e:
            print(f"Error enumerating kernel extensions: {e}")
            return []

    def _parse_kextstat_line(self, line: str) -> Dict:
        """
        Parse a single line from kextstat output

        Format: Index Refs Address Size Wired Name (Version) UUID <Linked Against>
        Example: 3  227 0  0  0  com.apple.kpi.bsd (25.2.0) UUID <>
        """
        try:
            # Split line into parts
            parts = line.split()

            if len(parts) < 6:
                return None

            # Parse index and refs
            index = int(parts[0])
            refs = int(parts[1])

            # Address (can be 0 or hex)
            address = parts[2]

            # Size and Wired (can be hex with 0x prefix or decimal)
            size_str = parts[3]
            wired_str = parts[4]

            # Convert to bytes (handle both hex and decimal)
            if size_str.startswith('0x'):
                size_bytes = int(size_str, 16)
            else:
                size_bytes = int(size_str)

            if wired_str.startswith('0x'):
                wired_bytes = int(wired_str, 16)
            else:
                wired_bytes = int(wired_str)

            # Extract bundle ID (it's the Name field, before the version in parentheses)
            # Find the part that looks like a bundle ID (com.apple.xxx)
            bundle_id = None
            for i, part in enumerate(parts[5:], 5):
                if part.startswith('com.') or part.startswith('org.'):
                    bundle_id = part
                    break

            if not bundle_id:
                return None

            # Convert to MB
            size_mb = round(size_bytes / (1024 * 1024), 3)
            wired_mb = round(wired_bytes / (1024 * 1024), 3)

            return {
                'index': index,
                'refs': refs,
                'address': address,
                'size_bytes': size_bytes,
                'size_mb': size_mb,
                'wired_bytes': wired_bytes,
                'wired_mb': wired_mb,
                'bundle_id': bundle_id
            }

        except Exception as e:
            # Skip malformed lines
            return None

    def categorize_kext(self, bundle_id: str) -> Tuple[str, str]:
        """
        Categorize a kernel extension by safety level

        Args:
            bundle_id: Bundle identifier of the kext

        Returns:
            Tuple of (category, reason)
            Categories: 'critical-system', 'critical-hardware', 'third-party', 'unknown'
        """
        # Check critical system patterns
        for pattern in self.CRITICAL_KEXT_PATTERNS:
            if re.match(pattern, bundle_id):
                return ('critical-system', 'System-critical kernel component')

        # Check hardware-specific patterns
        for pattern in self.PROTECTED_HARDWARE_PATTERNS:
            if re.match(pattern, bundle_id):
                return ('critical-hardware', 'Hardware driver required for operation')

        # Check for third-party kexts (non-Apple)
        if not bundle_id.startswith('com.apple.'):
            return ('third-party', 'Third-party kernel extension')

        # Apple kext but not in critical list
        return ('apple-non-critical', 'Apple extension, may be non-essential')

    def analyze_memory_usage(self) -> Dict:
        """
        Analyze kernel extension memory usage

        Returns:
            Comprehensive memory analysis with categorized kexts
        """
        kexts = self.enumerate_kernel_extensions()

        if not kexts:
            return {
                'timestamp': datetime.now().isoformat(),
                'error': 'Could not enumerate kernel extensions',
                'total_kexts': 0
            }

        # Categorize and analyze each kext
        categorized_kexts = {
            'critical-system': [],
            'critical-hardware': [],
            'apple-non-critical': [],
            'third-party': []
        }

        total_wired_memory_mb = 0
        memory_distribution = {
            'small': 0,      # <1 MB
            'medium': 0,     # 1-5 MB
            'large': 0,      # 5-50 MB
            'abnormal': 0    # >50 MB
        }

        for kext in kexts:
            category, reason = self.categorize_kext(kext['bundle_id'])
            wired_mb = kext['wired_mb']

            # Add category and reason to kext info
            kext['category'] = category
            kext['safety_reason'] = reason

            # Determine memory size category
            if wired_mb < self.memory_thresholds['small']:
                kext['memory_category'] = 'small'
                memory_distribution['small'] += 1
            elif wired_mb < self.memory_thresholds['medium']:
                kext['memory_category'] = 'medium'
                memory_distribution['medium'] += 1
            elif wired_mb < self.memory_thresholds['large']:
                kext['memory_category'] = 'large'
                memory_distribution['large'] += 1
            else:
                kext['memory_category'] = 'abnormal'
                memory_distribution['abnormal'] += 1

            categorized_kexts[category].append(kext)
            total_wired_memory_mb += wired_mb

        # Sort each category by wired memory (descending)
        for category in categorized_kexts:
            categorized_kexts[category].sort(key=lambda x: x['wired_mb'], reverse=True)

        return {
            'timestamp': datetime.now().isoformat(),
            'total_kexts': len(kexts),
            'total_wired_memory_mb': round(total_wired_memory_mb, 2),
            'memory_distribution': memory_distribution,
            'categorized_kexts': categorized_kexts,
            'category_counts': {
                'critical-system': len(categorized_kexts['critical-system']),
                'critical-hardware': len(categorized_kexts['critical-hardware']),
                'apple-non-critical': len(categorized_kexts['apple-non-critical']),
                'third-party': len(categorized_kexts['third-party'])
            }
        }

    def generate_recommendations(self, analysis: Dict) -> List[Dict]:
        """
        Generate safe kext unload recommendations

        Args:
            analysis: Output from analyze_memory_usage()

        Returns:
            List of recommendations
        """
        recommendations = []
        categorized = analysis.get('categorized_kexts', {})

        # Recommendation 1: Third-party kexts analysis
        third_party = categorized.get('third-party', [])
        if third_party:
            large_third_party = [k for k in third_party if k['wired_mb'] > 5]

            if large_third_party:
                total_memory = sum(k['wired_mb'] for k in large_third_party)
                recommendations.append({
                    'priority': 'medium',
                    'action': 'review_third_party_kexts',
                    'description': f"Found {len(large_third_party)} third-party kexts using significant memory",
                    'kexts': [f"{k['bundle_id']} ({k['wired_mb']:.2f} MB)" for k in large_third_party[:5]],
                    'total_memory_mb': round(total_memory, 2),
                    'safety_note': 'Third-party kexts can be unloaded, but may affect device/software functionality',
                    'method': 'Manual review required - use kextunload command'
                })

        # Recommendation 2: Abnormal memory usage
        abnormal_kexts = []
        for category, kexts in categorized.items():
            for kext in kexts:
                if kext['memory_category'] == 'abnormal' and category != 'critical-system':
                    abnormal_kexts.append(kext)

        if abnormal_kexts:
            abnormal_kexts.sort(key=lambda x: x['wired_mb'], reverse=True)
            total_memory = sum(k['wired_mb'] for k in abnormal_kexts)

            recommendations.append({
                'priority': 'high',
                'action': 'investigate_abnormal_memory',
                'description': f"Found {len(abnormal_kexts)} kexts with abnormal memory usage (>50 MB)",
                'kexts': [f"{k['bundle_id']} ({k['wired_mb']:.2f} MB)" for k in abnormal_kexts[:5]],
                'total_memory_mb': round(total_memory, 2),
                'investigation_note': 'These kexts may have memory leaks or inefficient memory management',
                'method': 'System reboot or contact vendor'
            })

        # Recommendation 3: System health check
        if analysis['total_wired_memory_mb'] > 500:
            recommendations.append({
                'priority': 'info',
                'action': 'kernel_memory_health',
                'description': f"Total kernel extension memory usage: {analysis['total_wired_memory_mb']:.2f} MB",
                'note': 'This is normal for modern macOS. Kernel extensions are wired memory and always resident.',
                'expected_range': '300-800 MB depending on hardware and installed drivers'
            })

        # Recommendation 4: No action needed
        if not recommendations:
            recommendations.append({
                'priority': 'low',
                'action': 'no_action_needed',
                'description': 'All kernel extensions are within normal parameters',
                'total_kexts': analysis['total_kexts'],
                'total_memory_mb': analysis['total_wired_memory_mb'],
                'note': 'Kernel extension memory is expected and necessary for system operation'
            })

        # Recommendation 5: Safety warning
        recommendations.append({
            'priority': 'critical',
            'action': 'safety_warning',
            'description': 'NEVER manually unload critical system kernel extensions',
            'critical_count': analysis['category_counts']['critical-system'] +
                            analysis['category_counts']['critical-hardware'],
            'warning': 'Unloading critical kexts will cause system crashes, data loss, or hardware failure',
            'protected_patterns': f"{len(self.CRITICAL_KEXT_PATTERNS)} critical patterns protected"
        })

        return recommendations

    def get_unload_instructions(self, bundle_id: str) -> Dict:
        """
        Get safe unload instructions for a specific kext

        Args:
            bundle_id: Bundle identifier of the kext to unload

        Returns:
            Unload instructions with safety checks
        """
        category, reason = self.categorize_kext(bundle_id)

        # Safety check
        if category in ['critical-system', 'critical-hardware']:
            return {
                'bundle_id': bundle_id,
                'safe_to_unload': False,
                'category': category,
                'reason': reason,
                'error': 'This is a critical kernel extension and MUST NOT be unloaded',
                'impact': 'System crash, hardware failure, data loss'
            }

        # Get current kext info
        kexts = self.enumerate_kernel_extensions()
        kext_info = next((k for k in kexts if k['bundle_id'] == bundle_id), None)

        if not kext_info:
            return {
                'bundle_id': bundle_id,
                'error': 'Kernel extension not found or not currently loaded'
            }

        # Generate unload instructions
        return {
            'bundle_id': bundle_id,
            'safe_to_unload': True,
            'category': category,
            'reason': reason,
            'current_memory_mb': kext_info['wired_mb'],
            'instructions': [
                '1. Save all work and close applications that might use this driver',
                f"2. Run: sudo kextunload -b {bundle_id}",
                '3. Verify unload: kextstat | grep {}'.format(bundle_id.split('.')[-1]),
                '4. To reload: sudo kextload /path/to/kext'
            ],
            'potential_recovery_mb': kext_info['wired_mb'],
            'warning': 'This will free wired memory but may disable associated hardware/software',
            'reboot_alternative': 'Consider rebooting instead for safer memory recovery'
        }

    def generate_report(self, output_path: Path = None, verbose: bool = False) -> str:
        """Generate kernel extension analysis report"""
        analysis = self.analyze_memory_usage()
        recommendations = self.generate_recommendations(analysis)

        report = {
            'analysis': analysis,
            'recommendations': recommendations,
            'verbose': verbose
        }

        # Add detailed kext list if verbose
        if verbose:
            report['detailed_kexts'] = analysis.get('categorized_kexts', {})

        report_json = json.dumps(report, indent=2)

        if output_path:
            try:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w') as f:
                    f.write(report_json)
                print(f"Report saved to: {output_path}")
            except Exception as e:
                print(f"Warning: Could not save report: {e}")

        return report_json


def main():
    """Main execution"""
    print("=== Kernel Extension Memory Analyzer (Agent 21) ===\n")

    # Parse command line args
    verbose = '--verbose' in sys.argv

    # Initialize analyzer
    analyzer = KextAnalyzer()

    # Analyze kernel extensions
    analysis = analyzer.analyze_memory_usage()

    # Display summary
    print(f"Timestamp: {analysis['timestamp']}\n")
    print(f"Total Kernel Extensions: {analysis['total_kexts']}")
    print(f"Total Wired Memory: {analysis['total_wired_memory_mb']:.2f} MB\n")

    # Display category breakdown
    print("=== Category Breakdown ===")
    counts = analysis['category_counts']
    print(f"  Critical System:     {counts['critical-system']:3d} kexts")
    print(f"  Critical Hardware:   {counts['critical-hardware']:3d} kexts")
    print(f"  Apple Non-Critical:  {counts['apple-non-critical']:3d} kexts")
    print(f"  Third-Party:         {counts['third-party']:3d} kexts\n")

    # Display memory distribution
    print("=== Memory Distribution ===")
    dist = analysis['memory_distribution']
    print(f"  Small (<1 MB):       {dist['small']:3d} kexts")
    print(f"  Medium (1-5 MB):     {dist['medium']:3d} kexts")
    print(f"  Large (5-50 MB):     {dist['large']:3d} kexts")
    print(f"  Abnormal (>50 MB):   {dist['abnormal']:3d} kexts\n")

    # Display top memory consumers (if verbose)
    if verbose:
        print("=== Top 10 Memory Consumers ===")
        all_kexts = []
        for category, kexts in analysis['categorized_kexts'].items():
            all_kexts.extend(kexts)
        all_kexts.sort(key=lambda x: x['wired_mb'], reverse=True)

        print(f"{'Bundle ID':60s}  {'Wired':>8s}  {'Category':>20s}")
        print("-" * 95)
        for kext in all_kexts[:10]:
            print(f"{kext['bundle_id']:60s}  {kext['wired_mb']:6.2f} MB  {kext['category']:>20s}")
        print()

    # Display third-party kexts (always show)
    third_party = analysis['categorized_kexts'].get('third-party', [])
    if third_party:
        print("=== Third-Party Kernel Extensions ===")
        print(f"{'Bundle ID':60s}  {'Wired':>8s}")
        print("-" * 75)
        for kext in third_party:
            print(f"{kext['bundle_id']:60s}  {kext['wired_mb']:6.2f} MB")
        print()

    # Generate and display recommendations
    recommendations = analyzer.generate_recommendations(analysis)
    print("=== Recommendations ===")
    for i, rec in enumerate(recommendations, 1):
        print(f"\n  {i}. [{rec['priority'].upper()}] {rec['description']}")
        print(f"     Action: {rec['action']}")

        if 'kexts' in rec:
            print(f"     Affected Kexts:")
            for kext in rec['kexts']:
                print(f"       - {kext}")
        if 'total_memory_mb' in rec:
            print(f"     Total Memory: {rec['total_memory_mb']:.2f} MB")
        if 'safety_note' in rec:
            print(f"     Safety: {rec['safety_note']}")
        if 'method' in rec:
            print(f"     Method: {rec['method']}")
        if 'warning' in rec:
            print(f"     ⚠️  WARNING: {rec['warning']}")
        if 'note' in rec:
            print(f"     Note: {rec['note']}")

    # Save report
    output_path = Path(__file__).parent.parent / 'data' / 'kernel-extension-analysis.json'
    analyzer.generate_report(output_path, verbose=verbose)

    print(f"\n💡 Expected Memory Recovery: 0-5 MB")
    print(f"   Note: Kernel extensions are necessary for system operation.")
    print(f"   Unloading kexts is generally NOT recommended for memory optimization.")
    print(f"\n💡 TIP: Run with --verbose flag for detailed kext information:")
    print(f"   python3 {Path(__file__).name} --verbose")

    return 0


if __name__ == '__main__':
    sys.exit(main())
