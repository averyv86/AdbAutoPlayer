#!/usr/bin/env python3
"""
Agent 25: Memory Compressor Analyzer
Analyzes macOS memory compression effectiveness
Part of macOS Resource Optimizer v2.0 - RAM Optimization Week 4
"""

import json
import sys
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict
from ram_utils import RAMUtils


class MemoryCompressorAnalyzer:
    """
    Analyzes macOS memory compression system effectiveness
    """

    def __init__(self, config_path: Path = None):
        """Initialize analyzer with configuration"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / 'config' / 'cleanup-rules.json'

        self.config = self._load_config(config_path)

        # Compression effectiveness thresholds
        self.good_compression_ratio = self.config.get('good_compression_ratio', 2.0)
        self.poor_compression_ratio = self.config.get('poor_compression_ratio', 1.3)

    def _load_config(self, config_path: Path) -> dict:
        """Load memory compression configuration"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                return config.get('memory_compression', {
                    'good_compression_ratio': 2.0,
                    'poor_compression_ratio': 1.3
                })
        except Exception as e:
            print(f"Warning: Could not load config: {e}")
            return {
                'good_compression_ratio': 2.0,
                'poor_compression_ratio': 1.3
            }

    def analyze_compression_effectiveness(self) -> dict:
        """
        Analyze memory compression system effectiveness
        Returns comprehensive compression analysis with optimization recommendations
        """
        # Get vm_stat output
        vm_stats = self._get_vm_statistics()

        if 'error' in vm_stats:
            return {
                'timestamp': datetime.now().isoformat(),
                'error': vm_stats['error']
            }

        # Parse compression statistics
        compression_stats = self._parse_compression_stats(vm_stats)

        # Calculate effectiveness metrics
        effectiveness = self._calculate_compression_effectiveness(compression_stats)

        # Get memory pressure
        pressure_level, pressure_stats = RAMUtils.get_memory_pressure()

        return {
            'timestamp': datetime.now().isoformat(),
            'compression_statistics': compression_stats,
            'compression_effectiveness': effectiveness,
            'memory_pressure': pressure_level,
            'vm_statistics': {
                'pages_free': vm_stats.get('pages_free', 0),
                'pages_active': vm_stats.get('pages_active', 0),
                'pages_inactive': vm_stats.get('pages_inactive', 0),
                'pages_wired': vm_stats.get('pages_wired_down', 0),
                'pageouts': vm_stats.get('pageouts', 0),
                'pageins': vm_stats.get('pageins', 0)
            },
            'recommendations': self._generate_recommendations(
                effectiveness, compression_stats, pressure_level
            )
        }

    def _get_vm_statistics(self) -> Dict:
        """Get virtual memory statistics from vm_stat"""
        try:
            result = subprocess.run(
                ['vm_stat'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return {'error': 'Could not get vm_stat'}

            # Parse vm_stat output
            stats = {}
            for line in result.stdout.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower().replace(' ', '_').replace('"', '')
                    value = value.strip().rstrip('.')

                    # Convert to integer (pages)
                    if value.isdigit():
                        stats[key] = int(value)

            return stats

        except Exception as e:
            return {'error': str(e)}

    def _parse_compression_stats(self, vm_stats: Dict) -> Dict:
        """Parse memory compression statistics from vm_stat"""
        # Page size (typically 4096 bytes)
        page_size_bytes = 4096

        # Compressed pages
        pages_stored_in_compressor = vm_stats.get('pages_stored_in_compressor', 0)
        pages_occupied_by_compressor = vm_stats.get('pages_occupied_by_compressor', 0)

        # Calculate sizes in GB
        compressed_data_gb = round((pages_stored_in_compressor * page_size_bytes) / (1024**3), 2)
        compressor_memory_gb = round((pages_occupied_by_compressor * page_size_bytes) / (1024**3), 2)

        # Calculate compression ratio
        compression_ratio = 0
        if pages_occupied_by_compressor > 0:
            compression_ratio = pages_stored_in_compressor / pages_occupied_by_compressor

        # Decompressions
        decompressions = vm_stats.get('decompressions', 0)
        compressions = vm_stats.get('compressions', 0)

        return {
            'pages_stored_in_compressor': pages_stored_in_compressor,
            'pages_occupied_by_compressor': pages_occupied_by_compressor,
            'compressed_data_gb': compressed_data_gb,
            'compressor_memory_gb': compressor_memory_gb,
            'compression_ratio': round(compression_ratio, 2),
            'space_saved_gb': round(compressed_data_gb - compressor_memory_gb, 2),
            'compressions': compressions,
            'decompressions': decompressions,
            'compression_activity': 'high' if compressions > 1000000 else 'moderate' if compressions > 100000 else 'low'
        }

    def _calculate_compression_effectiveness(self, compression_stats: Dict) -> Dict:
        """Calculate compression effectiveness metrics"""
        compression_ratio = compression_stats['compression_ratio']
        space_saved_gb = compression_stats['space_saved_gb']

        # Determine effectiveness level
        if compression_ratio >= self.good_compression_ratio:
            effectiveness_level = 'excellent'
            efficiency_percent = 90
        elif compression_ratio >= (self.good_compression_ratio + self.poor_compression_ratio) / 2:
            effectiveness_level = 'good'
            efficiency_percent = 70
        elif compression_ratio >= self.poor_compression_ratio:
            effectiveness_level = 'moderate'
            efficiency_percent = 50
        else:
            effectiveness_level = 'poor'
            efficiency_percent = 30

        # Calculate potential improvements
        if compression_ratio < self.good_compression_ratio:
            potential_improvement_gb = round(
                (compression_stats['compressed_data_gb'] / self.good_compression_ratio -
                 compression_stats['compressor_memory_gb']), 2
            )
        else:
            potential_improvement_gb = 0

        return {
            'effectiveness_level': effectiveness_level,
            'efficiency_percent': efficiency_percent,
            'compression_ratio': compression_ratio,
            'space_saved_gb': space_saved_gb,
            'potential_improvement_gb': max(0, potential_improvement_gb),
            'is_working_efficiently': compression_ratio >= self.poor_compression_ratio,
            'needs_optimization': compression_ratio < self.good_compression_ratio
        }

    def _generate_recommendations(self, effectiveness: Dict,
                                  compression_stats: Dict, pressure_level: str) -> list:
        """Generate compression optimization recommendations"""
        recommendations = []

        # Compression working well
        if effectiveness['effectiveness_level'] == 'excellent':
            return [{
                'priority': 'low',
                'action': 'no_action_needed',
                'description': 'Memory compression is working excellently',
                'compression_ratio': effectiveness['compression_ratio'],
                'space_saved_gb': effectiveness['space_saved_gb'],
                'note': f"Compressor is saving {effectiveness['space_saved_gb']} GB of RAM"
            }]

        # Poor compression - investigate
        if effectiveness['effectiveness_level'] in ['poor', 'moderate']:
            recommendations.append({
                'priority': 'high',
                'action': 'investigate_compression_inefficiency',
                'description': f"Compression effectiveness is {effectiveness['effectiveness_level']} (ratio: {effectiveness['compression_ratio']}x)",
                'current_ratio': effectiveness['compression_ratio'],
                'target_ratio': self.good_compression_ratio,
                'potential_improvement_gb': effectiveness['potential_improvement_gb'],
                'causes': [
                    'Incompressible data (encrypted files, compressed images/video)',
                    'High memory pressure preventing efficient compression',
                    'Too many active processes competing for compression',
                    'Specific applications with incompressible memory patterns'
                ],
                'risk': 'low',
                'impact': 'Better compression = more effective RAM'
            })

        # High compression activity with poor ratio
        if (compression_stats['compression_activity'] == 'high' and
            effectiveness['effectiveness_level'] in ['poor', 'moderate']):
            recommendations.append({
                'priority': 'high',
                'action': 'reduce_compression_overhead',
                'description': 'High compression activity with low effectiveness',
                'compressions': compression_stats['compressions'],
                'decompressions': compression_stats['decompressions'],
                'method': 'reduce_memory_pressure',
                'steps': [
                    'Run Week 2 browser optimization (reduce compressible data)',
                    'Run Week 3 app hibernation (free up RAM)',
                    'Close memory-intensive apps with incompressible data'
                ],
                'risk': 'low',
                'note': 'Reducing memory pressure improves compression efficiency'
            })

        # Memory pressure + poor compression
        if pressure_level in ['warning', 'critical'] and not effectiveness['is_working_efficiently']:
            recommendations.append({
                'priority': 'critical',
                'action': 'emergency_memory_optimization',
                'description': f"CRITICAL: {pressure_level.upper()} memory pressure + poor compression",
                'compression_ratio': effectiveness['compression_ratio'],
                'memory_pressure': pressure_level,
                'immediate_actions': [
                    'Run Agent 19 (Swap Optimizer) to reduce swap usage',
                    'Run Agent 16 (Electron App Optimizer) for immediate RAM recovery',
                    'Consider system restart to reset compression system'
                ],
                'risk': 'medium',
                'impact': 'Immediate performance improvement required',
                'estimated_time': '15-30 minutes'
            })

        # Optimization guidance
        if effectiveness['needs_optimization']:
            recommendations.append({
                'priority': 'medium',
                'action': 'optimize_compression_efficiency',
                'description': 'Improve compression effectiveness through RAM optimization',
                'strategies': [
                    {
                        'strategy': 'Reduce incompressible data',
                        'method': 'Close apps with encrypted/compressed data (videos, encrypted files)',
                        'expected_improvement': '0.2-0.5 compression ratio increase'
                    },
                    {
                        'strategy': 'Free up RAM',
                        'method': 'Run all Week 2-3 optimization agents',
                        'expected_improvement': f"{effectiveness['potential_improvement_gb']} GB better compression"
                    },
                    {
                        'strategy': 'Reset compression system',
                        'method': 'System restart (clears compression state)',
                        'expected_improvement': 'Fresh compression system initialization'
                    }
                ],
                'risk': 'low'
            })

        # Compression statistics interpretation
        recommendations.append({
            'priority': 'info',
            'action': 'understanding_compression',
            'description': 'Memory compression system overview',
            'explanation': {
                'compression_ratio': f"{effectiveness['compression_ratio']}x means {compression_stats['compressed_data_gb']} GB is compressed into {compression_stats['compressor_memory_gb']} GB",
                'space_saved': f"Compression is currently saving {compression_stats['space_saved_gb']} GB of RAM",
                'activity_level': f"Compression activity: {compression_stats['compression_activity']} ({compression_stats['compressions']:,} compressions, {compression_stats['decompressions']:,} decompressions)",
                'effectiveness': f"Compression effectiveness: {effectiveness['effectiveness_level']} ({effectiveness['efficiency_percent']}% efficient)"
            }
        })

        return recommendations

    def get_compression_health_report(self) -> dict:
        """Get comprehensive compression health report"""
        analysis = self.analyze_compression_effectiveness()

        if 'error' in analysis:
            return analysis

        effectiveness = analysis['compression_effectiveness']
        compression_stats = analysis['compression_statistics']

        # Health score (0-100)
        health_score = effectiveness['efficiency_percent']

        # Determine overall health
        if health_score >= 80:
            overall_health = 'healthy'
        elif health_score >= 60:
            overall_health = 'moderate'
        elif health_score >= 40:
            overall_health = 'poor'
        else:
            overall_health = 'critical'

        return {
            'overall_health': overall_health,
            'health_score': health_score,
            'compression_ratio': effectiveness['compression_ratio'],
            'space_saved_gb': effectiveness['space_saved_gb'],
            'is_working_efficiently': effectiveness['is_working_efficiently'],
            'needs_optimization': effectiveness['needs_optimization'],
            'memory_pressure': analysis['memory_pressure'],
            'activity_summary': {
                'compressions': compression_stats['compressions'],
                'decompressions': compression_stats['decompressions'],
                'activity_level': compression_stats['compression_activity']
            },
            'optimization_potential_gb': effectiveness['potential_improvement_gb'],
            'timestamp': datetime.now().isoformat()
        }

    def generate_report(self, output_path: Path = None) -> str:
        """Generate and save memory compression analysis report"""
        report = self.analyze_compression_effectiveness()
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
    print("=== Memory Compressor Analyzer (Agent 25) ===\n")

    # Initialize analyzer
    analyzer = MemoryCompressorAnalyzer()

    # Analyze compression
    report = analyzer.analyze_compression_effectiveness()

    if 'error' in report:
        print(f"Error: {report['error']}")
        return 1

    # Display compression statistics
    comp_stats = report['compression_statistics']
    print(f"Timestamp: {report['timestamp']}")
    print(f"Memory Pressure: {report['memory_pressure'].upper()}\n")

    print(f"=== Compression Statistics ===")
    print(f"Compressed Data: {comp_stats['compressed_data_gb']} GB ({comp_stats['pages_stored_in_compressor']:,} pages)")
    print(f"Compressor Memory: {comp_stats['compressor_memory_gb']} GB ({comp_stats['pages_occupied_by_compressor']:,} pages)")
    print(f"Compression Ratio: {comp_stats['compression_ratio']}x")
    print(f"Space Saved: {comp_stats['space_saved_gb']} GB\n")

    print(f"Compressions: {comp_stats['compressions']:,}")
    print(f"Decompressions: {comp_stats['decompressions']:,}")
    print(f"Activity Level: {comp_stats['compression_activity']}\n")

    # Display effectiveness
    effectiveness = report['compression_effectiveness']
    print(f"=== Compression Effectiveness ===")
    print(f"Effectiveness Level: {effectiveness['effectiveness_level'].upper()}")
    print(f"Efficiency: {effectiveness['efficiency_percent']}%")
    print(f"Working Efficiently: {'YES' if effectiveness['is_working_efficiently'] else 'NO'}")
    print(f"Needs Optimization: {'YES' if effectiveness['needs_optimization'] else 'NO'}")

    if effectiveness['potential_improvement_gb'] > 0:
        print(f"Potential Improvement: {effectiveness['potential_improvement_gb']} GB\n")
    else:
        print()

    # Display VM statistics
    vm_stats = report['vm_statistics']
    print(f"=== VM Statistics ===")
    print(f"Free Pages: {vm_stats['pages_free']:,}")
    print(f"Active Pages: {vm_stats['pages_active']:,}")
    print(f"Inactive Pages: {vm_stats['pages_inactive']:,}")
    print(f"Wired Pages: {vm_stats['pages_wired']:,}")
    print(f"Pageins: {vm_stats['pageins']:,}")
    print(f"Pageouts: {vm_stats['pageouts']:,}\n")

    # Display recommendations
    if report['recommendations']:
        print(f"=== Recommendations ===")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"\n  {i}. [{rec['priority'].upper()}] {rec['description']}")
            print(f"     Action: {rec['action']}")

            if 'current_ratio' in rec:
                print(f"     Current Ratio: {rec['current_ratio']}x")
            if 'target_ratio' in rec:
                print(f"     Target Ratio: {rec['target_ratio']}x")
            if 'space_saved_gb' in rec:
                print(f"     Space Saved: {rec['space_saved_gb']} GB")
            if 'potential_improvement_gb' in rec:
                print(f"     Potential Improvement: {rec['potential_improvement_gb']} GB")
            if 'causes' in rec:
                print(f"     Possible Causes:")
                for cause in rec['causes']:
                    print(f"       - {cause}")
            if 'steps' in rec:
                print(f"     Steps:")
                for step in rec['steps']:
                    print(f"       - {step}")
            if 'immediate_actions' in rec:
                print(f"     Immediate Actions:")
                for action in rec['immediate_actions']:
                    print(f"       - {action}")
            if 'strategies' in rec:
                print(f"     Optimization Strategies:")
                for strat in rec['strategies']:
                    print(f"       - {strat['strategy']}: {strat['method']}")
                    print(f"         Expected: {strat['expected_improvement']}")
            if 'explanation' in rec:
                print(f"     Explanation:")
                for key, value in rec['explanation'].items():
                    print(f"       - {key.replace('_', ' ').title()}: {value}")
            if 'method' in rec:
                print(f"     Method: {rec['method']}")
            if 'risk' in rec:
                print(f"     Risk: {rec['risk']}")
            if 'impact' in rec:
                print(f"     Impact: {rec['impact']}")
            if 'estimated_time' in rec:
                print(f"     Est. Time: {rec['estimated_time']}")
            if 'note' in rec:
                print(f"     Note: {rec['note']}")

    # Get health report
    print(f"\n=== Compression Health Report ===")
    health = analyzer.get_compression_health_report()
    print(f"Overall Health: {health['overall_health'].upper()}")
    print(f"Health Score: {health['health_score']}/100")
    print(f"Compression Ratio: {health['compression_ratio']}x")
    print(f"Space Saved: {health['space_saved_gb']} GB")

    if health['optimization_potential_gb'] > 0:
        print(f"Optimization Potential: {health['optimization_potential_gb']} GB")

    # Save report
    output_path = Path(__file__).parent.parent / 'data' / 'memory-compression-analysis.json'
    analyzer.generate_report(output_path)

    return 0


if __name__ == '__main__':
    sys.exit(main())
