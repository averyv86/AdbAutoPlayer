#!/usr/bin/env python3
"""
Agent 22: WindowServer Optimizer
Analyzes and optimizes WindowServer memory usage
Part of macOS Resource Optimizer v2.0 - RAM Optimization Week 4
"""

import json
import sys
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict
from ram_utils import RAMUtils


class WindowServerOptimizer:
    """
    Optimizes WindowServer memory usage (display system process)
    """

    def __init__(self, config_path: Path = None):
        """Initialize optimizer with configuration"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / 'config' / 'cleanup-rules.json'

        self.config = self._load_config(config_path)

        # WindowServer thresholds
        self.normal_memory_gb = self.config.get('normal_windowserver_memory_gb', 1.5)
        self.warning_memory_gb = self.config.get('warning_windowserver_memory_gb', 2.5)
        self.critical_memory_gb = self.config.get('critical_windowserver_memory_gb', 4.0)

    def _load_config(self, config_path: Path) -> dict:
        """Load WindowServer optimization configuration"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                return config.get('windowserver_optimization', {
                    'normal_windowserver_memory_gb': 1.5,
                    'warning_windowserver_memory_gb': 2.5,
                    'critical_windowserver_memory_gb': 4.0
                })
        except Exception as e:
            print(f"Warning: Could not load config: {e}")
            return {
                'normal_windowserver_memory_gb': 1.5,
                'warning_windowserver_memory_gb': 2.5,
                'critical_windowserver_memory_gb': 4.0
            }

    def analyze_windowserver(self) -> dict:
        """
        Analyze WindowServer memory usage and identify optimization opportunities
        Returns comprehensive WindowServer analysis with optimization recommendations
        """
        # Get WindowServer process info
        windowserver_info = self._get_windowserver_info()

        if 'error' in windowserver_info:
            return {
                'timestamp': datetime.now().isoformat(),
                'error': windowserver_info['error']
            }

        memory_gb = windowserver_info['memory_gb']

        # Determine severity
        if memory_gb >= self.critical_memory_gb:
            severity = 'critical'
        elif memory_gb >= self.warning_memory_gb:
            severity = 'warning'
        elif memory_gb >= self.normal_memory_gb:
            severity = 'elevated'
        else:
            severity = 'normal'

        # Get display configuration
        display_config = self._get_display_configuration()

        # Calculate optimization potential
        if severity in ['critical', 'warning']:
            potential_savings = max(0, memory_gb - self.normal_memory_gb)
        elif severity == 'elevated':
            potential_savings = max(0, memory_gb - self.normal_memory_gb) * 0.5
        else:
            potential_savings = 0

        return {
            'timestamp': datetime.now().isoformat(),
            'windowserver_info': windowserver_info,
            'severity': severity,
            'display_configuration': display_config,
            'thresholds': {
                'normal_gb': self.normal_memory_gb,
                'warning_gb': self.warning_memory_gb,
                'critical_gb': self.critical_memory_gb
            },
            'optimization_analysis': {
                'current_memory_gb': memory_gb,
                'target_memory_gb': self.normal_memory_gb,
                'potential_savings_gb': round(potential_savings, 2),
                'reduction_percent': round((potential_savings / memory_gb * 100), 1) if memory_gb > 0 else 0
            },
            'recommendations': self._generate_recommendations(
                memory_gb, severity, display_config, potential_savings
            )
        }

    def _get_windowserver_info(self) -> Dict:
        """Get WindowServer process information"""
        try:
            result = subprocess.run(
                ['ps', 'aux'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return {'error': 'Could not get process list'}

            # Find WindowServer process
            for line in result.stdout.split('\n'):
                if 'WindowServer' in line and '/System/' in line:
                    parts = line.split(None, 10)
                    if len(parts) < 11:
                        continue

                    pid = int(parts[1])
                    cpu_percent = float(parts[2])
                    rss_kb = float(parts[5])
                    memory_gb = round(rss_kb / 1024 / 1024, 2)
                    memory_percent = float(parts[3])

                    return {
                        'pid': pid,
                        'memory_gb': memory_gb,
                        'memory_percent': memory_percent,
                        'cpu_percent': cpu_percent,
                        'process_name': 'WindowServer'
                    }

            return {'error': 'WindowServer process not found'}

        except Exception as e:
            return {'error': str(e)}

    def _get_display_configuration(self) -> Dict:
        """Get current display configuration"""
        try:
            # Get display info using system_profiler
            result = subprocess.run(
                ['system_profiler', 'SPDisplaysDataType', '-json'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return {'error': 'Could not get display info'}

            display_data = json.loads(result.stdout)

            displays = []
            display_count = 0

            # Parse display data
            if 'SPDisplaysDataType' in display_data:
                for display_info in display_data['SPDisplaysDataType']:
                    if 'spdisplays_ndrvs' in display_info:
                        for display in display_info['spdisplays_ndrvs']:
                            display_count += 1

                            resolution = display.get('_spdisplays_resolution', 'Unknown')
                            pixel_depth = display.get('spdisplays_depth', 'Unknown')
                            main_display = display.get('spdisplays_main', 'no') == 'yes'

                            displays.append({
                                'display_number': display_count,
                                'resolution': resolution,
                                'pixel_depth': pixel_depth,
                                'is_main': main_display
                            })

            return {
                'display_count': display_count,
                'displays': displays,
                'configuration': 'single' if display_count == 1 else 'multiple',
                'high_resolution': any('Retina' in str(d) or '4K' in str(d) or '5K' in str(d)
                                     for d in displays)
            }

        except Exception as e:
            # Fallback: Try to count displays using a simpler method
            try:
                result = subprocess.run(
                    ['system_profiler', 'SPDisplaysDataType'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                display_count = result.stdout.count('Resolution:')

                return {
                    'display_count': display_count,
                    'displays': [],
                    'configuration': 'single' if display_count == 1 else 'multiple',
                    'high_resolution': 'Retina' in result.stdout or '4K' in result.stdout
                }
            except:
                return {
                    'display_count': 1,
                    'displays': [],
                    'configuration': 'unknown',
                    'error': str(e)
                }

    def _generate_recommendations(self, memory_gb: float, severity: str,
                                  display_config: Dict, potential_savings: float) -> list:
        """Generate WindowServer optimization recommendations"""
        if severity == 'normal':
            return [{
                'priority': 'low',
                'action': 'no_action_needed',
                'description': 'WindowServer memory usage is normal',
                'current_memory_gb': memory_gb,
                'target_memory_gb': self.normal_memory_gb
            }]

        recommendations = []

        # Critical/Warning: Immediate optimization
        if severity in ['critical', 'warning']:
            recommendations.append({
                'priority': 'critical' if severity == 'critical' else 'high',
                'action': 'reduce_display_buffer_memory',
                'description': f"{severity.upper()}: Reduce WindowServer memory from {memory_gb} GB to {self.normal_memory_gb} GB",
                'expected_savings_gb': round(potential_savings, 2),
                'steps': [
                    'Reduce display resolution if using scaled/high-DPI',
                    'Close unnecessary windows',
                    'Reduce transparency/visual effects',
                    'Restart WindowServer (requires logout)'
                ],
                'risk': 'low',
                'impact': 'Reduced visual quality, improved performance'
            })

        # Multiple displays optimization
        if display_config.get('display_count', 1) > 1:
            recommendations.append({
                'priority': 'high',
                'action': 'optimize_multi_display_setup',
                'description': f"Optimize {display_config['display_count']}-display configuration",
                'method': 'reduce_display_count_or_resolution',
                'expected_savings_gb': round(potential_savings * 0.4, 2),
                'risk': 'low',
                'impact': 'Disconnect external display(s) when not needed',
                'note': 'Each additional display adds ~300-500 MB to WindowServer'
            })

        # High resolution optimization
        if display_config.get('high_resolution', False):
            recommendations.append({
                'priority': 'medium',
                'action': 'reduce_display_resolution',
                'description': 'Reduce scaled/Retina resolution to native',
                'method': 'display_settings_adjustment',
                'expected_savings_gb': round(potential_savings * 0.3, 2),
                'steps': [
                    'System Preferences → Displays',
                    'Select "Default for display" instead of "Scaled"',
                    'Or choose lower resolution'
                ],
                'risk': 'very_low',
                'impact': 'Slightly larger UI elements, reduced memory usage'
            })

        # Visual effects optimization
        if memory_gb > 2.0:
            recommendations.append({
                'priority': 'medium',
                'action': 'reduce_visual_effects',
                'description': 'Reduce transparency and visual effects',
                'method': 'accessibility_settings',
                'expected_savings_gb': round(potential_savings * 0.2, 2),
                'steps': [
                    'System Preferences → Accessibility → Display',
                    'Enable "Reduce transparency"',
                    'Enable "Reduce motion"'
                ],
                'risk': 'very_low',
                'impact': 'Less fancy animations, improved performance'
            })

        # Window management
        recommendations.append({
            'priority': 'low',
            'action': 'close_unnecessary_windows',
            'description': 'Close unused application windows',
            'method': 'manual_window_management',
            'expected_savings_gb': round(potential_savings * 0.1, 2),
            'risk': 'very_low',
            'impact': 'Reduced window buffer memory'
        })

        # Restart WindowServer (last resort)
        if severity == 'critical':
            recommendations.append({
                'priority': 'high',
                'action': 'restart_windowserver',
                'description': 'Restart WindowServer to clear memory buffers',
                'method': 'forced_restart',
                'command': 'sudo killall -HUP WindowServer',
                'expected_savings_gb': round(potential_savings * 0.5, 2),
                'risk': 'medium',
                'impact': 'Logs out current user, closes all applications',
                'note': 'SAVE ALL WORK FIRST - This will log you out'
            })

        return recommendations

    def get_optimization_guide(self) -> dict:
        """Get comprehensive WindowServer optimization guide"""
        analysis = self.analyze_windowserver()

        if 'error' in analysis:
            return analysis

        return {
            'current_state': {
                'memory_gb': analysis['windowserver_info']['memory_gb'],
                'severity': analysis['severity'],
                'display_count': analysis['display_configuration'].get('display_count', 1)
            },
            'optimization_strategies': [
                {
                    'strategy': 'Display Resolution Optimization',
                    'impact': 'High',
                    'difficulty': 'Easy',
                    'savings_potential_gb': '0.5-1.0',
                    'steps': [
                        'Open System Preferences → Displays',
                        'Select "Default for display" (native resolution)',
                        'Avoid "Scaled" options that require additional rendering'
                    ]
                },
                {
                    'strategy': 'Multi-Display Management',
                    'impact': 'High',
                    'difficulty': 'Easy',
                    'savings_potential_gb': '0.3-0.5 per display',
                    'steps': [
                        'Disconnect external displays when not in use',
                        'Use Spaces/Mission Control instead of multiple displays',
                        'Consider lower resolution for secondary displays'
                    ]
                },
                {
                    'strategy': 'Visual Effects Reduction',
                    'impact': 'Medium',
                    'difficulty': 'Easy',
                    'savings_potential_gb': '0.2-0.4',
                    'steps': [
                        'System Preferences → Accessibility → Display',
                        'Enable "Reduce transparency"',
                        'Enable "Reduce motion"'
                    ]
                },
                {
                    'strategy': 'Window Management',
                    'impact': 'Low',
                    'difficulty': 'Easy',
                    'savings_potential_gb': '0.1-0.2',
                    'steps': [
                        'Close unused windows regularly',
                        'Minimize windows instead of keeping them open',
                        'Use Cmd+H to hide applications instead of keeping visible'
                    ]
                }
            ],
            'timestamp': datetime.now().isoformat()
        }

    def generate_report(self, output_path: Path = None) -> str:
        """Generate and save WindowServer optimization report"""
        report = self.analyze_windowserver()
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
    print("=== WindowServer Optimizer (Agent 22) ===\n")

    # Initialize optimizer
    optimizer = WindowServerOptimizer()

    # Analyze WindowServer
    report = optimizer.analyze_windowserver()

    if 'error' in report:
        print(f"Error: {report['error']}")
        return 1

    # Display WindowServer info
    ws_info = report['windowserver_info']
    print(f"Timestamp: {report['timestamp']}")
    print(f"Process: {ws_info['process_name']} (PID {ws_info['pid']})")
    print(f"Memory: {ws_info['memory_gb']} GB ({ws_info['memory_percent']}%)")
    print(f"CPU: {ws_info['cpu_percent']}%\n")

    print(f"Severity: {report['severity'].upper()}\n")

    # Display thresholds
    thresholds = report['thresholds']
    print(f"=== Memory Thresholds ===")
    print(f"Normal: ≤{thresholds['normal_gb']} GB")
    print(f"Warning: {thresholds['warning_gb']} GB")
    print(f"Critical: ≥{thresholds['critical_gb']} GB\n")

    # Display configuration
    display_config = report['display_configuration']
    print(f"=== Display Configuration ===")
    print(f"Display Count: {display_config.get('display_count', 'Unknown')}")
    print(f"Configuration: {display_config.get('configuration', 'Unknown')}")
    print(f"High Resolution: {'Yes' if display_config.get('high_resolution') else 'No'}")

    if display_config.get('displays'):
        print(f"\nDisplays:")
        for display in display_config['displays']:
            main_str = " (Main)" if display.get('is_main') else ""
            print(f"  {display['display_number']}.{main_str} {display.get('resolution', 'Unknown')} - {display.get('pixel_depth', 'Unknown')}")
    print()

    # Display optimization analysis
    opt = report['optimization_analysis']
    print(f"=== Optimization Analysis ===")
    print(f"Current Memory: {opt['current_memory_gb']} GB")
    print(f"Target Memory: {opt['target_memory_gb']} GB")
    print(f"Potential Savings: {opt['potential_savings_gb']} GB ({opt['reduction_percent']}%)\n")

    # Display recommendations
    if report['recommendations']:
        print(f"=== Recommendations ===")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"\n  {i}. [{rec['priority'].upper()}] {rec['description']}")
            print(f"     Action: {rec['action']}")

            if 'expected_savings_gb' in rec:
                print(f"     Expected Savings: {rec['expected_savings_gb']} GB")
            if 'steps' in rec:
                print(f"     Steps:")
                for step in rec['steps']:
                    print(f"       - {step}")
            if 'method' in rec:
                print(f"     Method: {rec['method']}")
            if 'command' in rec:
                print(f"     Command: {rec['command']}")
            if 'risk' in rec:
                print(f"     Risk: {rec['risk']}")
            if 'impact' in rec:
                print(f"     Impact: {rec['impact']}")
            if 'note' in rec:
                print(f"     Note: {rec['note']}")

    # Save report
    output_path = Path(__file__).parent.parent / 'data' / 'windowserver-optimization.json'
    optimizer.generate_report(output_path)

    return 0


if __name__ == '__main__':
    sys.exit(main())
