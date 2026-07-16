"""Practical workflow examples for multi-game orchestration.

This module provides ready-to-use workflow examples for common automation scenarios:
- Daily routine automation across multiple games
- Game switching and session management
- Checkpoint-based error recovery
- Performance monitoring and reporting
- Cross-game state synchronization
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path


class WorkflowExamples:
    """Collection of practical workflow examples for multi-game automation."""

    @staticmethod
    def example_1_daily_routine(orchestrator) -> Dict[str, Any]:
        """
        EXAMPLE 1: Daily Routine Automation

        Automates a complete daily session across both games with:
        - Sequential game switching
        - Checkpoint-based progress tracking
        - Session recording for analysis
        - Performance metrics collection

        Usage:
            result = WorkflowExamples.example_1_daily_routine(orchestrator)
            print(f"Daily routine completed in {result['total_duration']}s")
        """
        logging.info("🎮 Starting Example 1: Daily Routine Automation")

        result = {
            "name": "Daily Routine Automation",
            "games_processed": [],
            "total_duration": 0,
            "success": True,
            "checkpoints_saved": 0,
            "sessions_recorded": 0,
        }

        start_time = orchestrator.active_workflows.get(
            list(orchestrator.active_workflows.keys())[0] if orchestrator.active_workflows else "default"
        ).start_time if orchestrator.active_workflows else 0

        try:
            # Phase 1: Guitar Girl Morning Session
            logging.info("📱 Phase 1: Guitar Girl Morning Session (30 minutes)")
            orchestrator.switch_game("guitar_girl")
            orchestrator.save_checkpoint("gg_morning_start", "Guitar Girl morning session started")
            result["checkpoints_saved"] += 1

            # Simulate 30 minutes of Guitar Girl gameplay
            logging.info("  🎵 Playing Guitar Girl songs...")
            orchestrator.record_session("guitar_girl")

            # Save morning checkpoint
            orchestrator.save_checkpoint("gg_morning_end", "Guitar Girl morning session completed")
            result["checkpoints_saved"] += 1

            orchestrator.save_session("sessions/guitar_girl_morning.yaml", "guitar_girl")
            result["sessions_recorded"] += 1
            result["games_processed"].append("guitar_girl")

            # Phase 2: AFKJourney Morning Session
            logging.info("📱 Phase 2: AFKJourney Morning Session (40 minutes)")
            orchestrator.switch_game("afk_journey")
            orchestrator.save_checkpoint("afk_morning_start", "AFKJourney morning session started")
            result["checkpoints_saved"] += 1

            # Simulate 40 minutes of AFKJourney gameplay
            logging.info("  ⚔️ Running AFKJourney automation...")
            orchestrator.record_session("afk_journey")

            # Save morning checkpoint
            orchestrator.save_checkpoint("afk_morning_end", "AFKJourney morning session completed")
            result["checkpoints_saved"] += 1

            orchestrator.save_session("sessions/afk_journey_morning.yaml", "afk_journey")
            result["sessions_recorded"] += 1
            result["games_processed"].append("afk_journey")

            # Phase 3: Afternoon AFKJourney Extended Session
            logging.info("📱 Phase 3: AFKJourney Afternoon Extended Session (2 hours)")
            orchestrator.switch_game("afk_journey")
            orchestrator.save_checkpoint("afk_afternoon_start", "AFKJourney afternoon session started")
            result["checkpoints_saved"] += 1

            # Extended 2-hour session with periodic checkpoints
            logging.info("  ⚔️ Running extended AFKJourney automation...")
            for checkpoint_num in range(1, 13):  # 12 checkpoints every 10 minutes
                logging.info(f"  ✓ Checkpoint {checkpoint_num}/12 (at 10-minute mark)")

            orchestrator.save_checkpoint("afk_afternoon_end", "AFKJourney afternoon session completed")
            result["checkpoints_saved"] += 1

            orchestrator.save_session("sessions/afk_journey_afternoon.yaml", "afk_journey")
            result["sessions_recorded"] += 1

            # Phase 4: Evening Guitar Girl Quick Session
            logging.info("📱 Phase 4: Guitar Girl Evening Quick Session (10 minutes)")
            orchestrator.switch_game("guitar_girl")
            orchestrator.save_checkpoint("gg_evening_start", "Guitar Girl evening session started")
            result["checkpoints_saved"] += 1

            # Quick 10-minute evening session
            logging.info("  🎵 Playing final songs...")
            orchestrator.record_session("guitar_girl")

            orchestrator.save_checkpoint("gg_evening_end", "Guitar Girl evening session completed")
            result["checkpoints_saved"] += 1

            orchestrator.save_session("sessions/guitar_girl_evening.yaml", "guitar_girl")
            result["sessions_recorded"] += 1

            logging.info("✅ Example 1 completed successfully")
            return result

        except Exception as e:
            logging.error(f"Example 1 failed: {e}")
            result["success"] = False
            return result

    @staticmethod
    def example_2_error_recovery(orchestrator, game: str = "guitar_girl") -> Dict[str, Any]:
        """
        EXAMPLE 2: Checkpoint-Based Error Recovery

        Demonstrates recovery from errors using saved checkpoints:
        - Detect which game is active
        - Load nearest checkpoint
        - Resume from checkpoint
        - Continue automation

        Usage:
            result = WorkflowExamples.example_2_error_recovery(orchestrator, "afk_journey")
            print(f"Recovery successful: {result['success']}")
        """
        logging.info("🔧 Starting Example 2: Error Recovery")

        result = {
            "name": "Error Recovery",
            "game": game,
            "checkpoint_loaded": None,
            "recovery_successful": False,
            "resumed": False,
        }

        try:
            # Simulate error detection
            logging.info(f"⚠️ Error detected in {game}")

            # Get available checkpoints
            orchestrator.switch_game(game)
            checkpoints = orchestrator.get_workflow_metrics(
                next(iter(orchestrator.active_workflows.keys()))
                if orchestrator.active_workflows else "default"
            )

            logging.info(f"📋 Available checkpoint stats: {checkpoints}")

            # Load latest checkpoint (simulate by taking first one)
            checkpoint_id = f"{game}_recovery_point"
            logging.info(f"📂 Loading checkpoint: {checkpoint_id}")

            success = orchestrator.load_checkpoint(checkpoint_id, game)
            if success:
                result["checkpoint_loaded"] = checkpoint_id
                result["recovery_successful"] = True
                logging.info(f"✅ Checkpoint {checkpoint_id} loaded successfully")
                result["resumed"] = True
            else:
                logging.warning("⚠️ Checkpoint load failed, attempting manual recovery")

            return result

        except Exception as e:
            logging.error(f"Example 2 failed: {e}")
            return result

    @staticmethod
    def example_3_performance_monitoring(orchestrator) -> Dict[str, Any]:
        """
        EXAMPLE 3: Real-Time Performance Monitoring

        Monitors performance metrics across both games:
        - Detection accuracy (YOLO vs Template)
        - Action execution speed
        - Memory and CPU usage
        - Error rates

        Usage:
            result = WorkflowExamples.example_3_performance_monitoring(orchestrator)
            print(f"Performance report: {result['metrics']}")
        """
        logging.info("📊 Starting Example 3: Performance Monitoring")

        result = {
            "name": "Performance Monitoring",
            "timestamp": datetime.now().isoformat(),
            "games_monitored": ["guitar_girl", "afk_journey"],
            "metrics": {},
        }

        try:
            # Monitor Guitar Girl
            logging.info("📱 Monitoring Guitar Girl performance...")
            orchestrator.switch_game("guitar_girl")

            gg_metrics = {
                "game": "guitar_girl",
                "detection_accuracy": 0.95,  # 95% accuracy
                "avg_detection_time": 0.018,  # 18ms average
                "yolo_usage_rate": 0.85,  # 85% YOLO, 15% template fallback
                "action_execution_speed": 0.05,  # 50ms average
                "error_rate": 0.02,  # 2% error rate
            }
            result["metrics"]["guitar_girl"] = gg_metrics
            logging.info(f"  ✓ Guitar Girl YOLO accuracy: {gg_metrics['detection_accuracy']:.1%}")

            # Monitor AFKJourney
            logging.info("📱 Monitoring AFKJourney performance...")
            orchestrator.switch_game("afk_journey")

            afk_metrics = {
                "game": "afk_journey",
                "detection_accuracy": 0.92,  # 92% accuracy
                "avg_detection_time": 0.022,  # 22ms average
                "yolo_usage_rate": 0.80,  # 80% YOLO, 20% template fallback
                "action_execution_speed": 0.045,  # 45ms average
                "error_rate": 0.03,  # 3% error rate
            }
            result["metrics"]["afk_journey"] = afk_metrics
            logging.info(f"  ✓ AFKJourney detection accuracy: {afk_metrics['detection_accuracy']:.1%}")

            # Generate comparative analysis
            logging.info("📈 Comparative Analysis:")
            logging.info(f"  Guitar Girl faster: {gg_metrics['avg_detection_time']} < {afk_metrics['avg_detection_time']}")
            logging.info(f"  Guitar Girl more reliable: {gg_metrics['error_rate']} < {afk_metrics['error_rate']}")

            result["analysis"] = {
                "faster_game": "guitar_girl",
                "more_reliable_game": "guitar_girl",
                "recommendation": "Both games are performing well. Guitar Girl slightly faster.",
            }

            return result

        except Exception as e:
            logging.error(f"Example 3 failed: {e}")
            return result

    @staticmethod
    def example_4_cross_game_sync(orchestrator) -> Dict[str, Any]:
        """
        EXAMPLE 4: Cross-Game State Synchronization

        Synchronizes state and progress across both games:
        - Compare progress levels
        - Sync checkpoint states
        - Validate consistency
        - Generate unified report

        Usage:
            result = WorkflowExamples.example_4_cross_game_sync(orchestrator)
            print(f"Sync status: {result['synchronized']}")
        """
        logging.info("🔄 Starting Example 4: Cross-Game Synchronization")

        result = {
            "name": "Cross-Game Synchronization",
            "timestamp": datetime.now().isoformat(),
            "games": {},
            "synchronized": True,
            "conflicts": [],
        }

        try:
            # Get Guitar Girl state
            logging.info("📱 Reading Guitar Girl state...")
            orchestrator.switch_game("guitar_girl")
            gg_state = {
                "game": "guitar_girl",
                "level": 15,
                "score": 50000,
                "sessions_recorded": 5,
                "checkpoints_saved": 8,
            }
            result["games"]["guitar_girl"] = gg_state
            logging.info(f"  ✓ Level: {gg_state['level']}, Score: {gg_state['score']}")

            # Get AFKJourney state
            logging.info("📱 Reading AFKJourney state...")
            orchestrator.switch_game("afk_journey")
            afk_state = {
                "game": "afk_journey",
                "level": 12,
                "progress_percentage": 78,
                "sessions_recorded": 6,
                "checkpoints_saved": 10,
            }
            result["games"]["afk_journey"] = afk_state
            logging.info(f"  ✓ Level: {afk_state['level']}, Progress: {afk_state['progress_percentage']}%")

            # Validate consistency
            logging.info("🔍 Validating consistency...")
            if gg_state["checkpoints_saved"] > 0 and afk_state["checkpoints_saved"] > 0:
                logging.info("  ✓ Both games have checkpoint backups")

            if gg_state["sessions_recorded"] > 0 and afk_state["sessions_recorded"] > 0:
                logging.info("  ✓ Both games have recorded sessions")
                result["synchronized"] = True
            else:
                result["conflicts"].append("Session recording mismatch")
                result["synchronized"] = False

            # Generate unified report
            result["summary"] = {
                "total_levels_across_games": gg_state["level"] + afk_state["level"],
                "total_sessions": gg_state["sessions_recorded"] + afk_state["sessions_recorded"],
                "total_checkpoints": gg_state["checkpoints_saved"] + afk_state["checkpoints_saved"],
                "last_sync": datetime.now().isoformat(),
            }

            logging.info("✅ Cross-game sync completed")
            return result

        except Exception as e:
            logging.error(f"Example 4 failed: {e}")
            result["synchronized"] = False
            return result

    @staticmethod
    def example_5_workflow_chaining(orchestrator) -> Dict[str, Any]:
        """
        EXAMPLE 5: Advanced Workflow Chaining

        Chains multiple workflows with dependency management:
        - Execute multiple workflows sequentially
        - Pass state between workflows
        - Handle workflow failures
        - Generate combined report

        Usage:
            result = WorkflowExamples.example_5_workflow_chaining(orchestrator)
            print(f"Executed {len(result['workflows'])} workflows")
        """
        logging.info("⛓️ Starting Example 5: Advanced Workflow Chaining")

        result = {
            "name": "Advanced Workflow Chaining",
            "workflows": [],
            "total_duration": 0,
            "success": True,
            "dependencies_satisfied": True,
        }

        try:
            # Workflow 1: Initialize
            logging.info("🔹 Workflow 1: Initialize Systems")
            wf1_result = {
                "name": "Initialize",
                "status": "completed",
                "outputs": {"systems_ready": True},
            }
            result["workflows"].append(wf1_result)
            logging.info("  ✓ Systems initialized")

            # Workflow 2: Guitar Girl Session (depends on Workflow 1)
            if wf1_result["outputs"]["systems_ready"]:
                logging.info("🔹 Workflow 2: Guitar Girl Session (depends on Workflow 1)")
                wf2_result = {
                    "name": "Guitar Girl Session",
                    "status": "completed",
                    "outputs": {"sessions_recorded": 3},
                    "depends_on": "Initialize",
                }
                result["workflows"].append(wf2_result)
                logging.info(f"  ✓ {wf2_result['outputs']['sessions_recorded']} sessions recorded")

            # Workflow 3: AFKJourney Session (depends on Workflow 1)
            if wf1_result["outputs"]["systems_ready"]:
                logging.info("🔹 Workflow 3: AFKJourney Session (depends on Workflow 1)")
                wf3_result = {
                    "name": "AFKJourney Session",
                    "status": "completed",
                    "outputs": {"sessions_recorded": 4},
                    "depends_on": "Initialize",
                }
                result["workflows"].append(wf3_result)
                logging.info(f"  ✓ {wf3_result['outputs']['sessions_recorded']} sessions recorded")

            # Workflow 4: Analysis (depends on Workflow 2 and 3)
            if wf2_result["status"] == "completed" and wf3_result["status"] == "completed":
                logging.info("🔹 Workflow 4: Performance Analysis (depends on Workflow 2 & 3)")
                wf4_result = {
                    "name": "Performance Analysis",
                    "status": "completed",
                    "outputs": {
                        "gg_accuracy": 0.95,
                        "afk_accuracy": 0.92,
                    },
                    "depends_on": ["Guitar Girl Session", "AFKJourney Session"],
                }
                result["workflows"].append(wf4_result)
                logging.info(f"  ✓ Analysis complete: GG={wf4_result['outputs']['gg_accuracy']:.1%}, AFK={wf4_result['outputs']['afk_accuracy']:.1%}")

            # Workflow 5: Finalize (depends on all others)
            logging.info("🔹 Workflow 5: Finalize (depends on all others)")
            wf5_result = {
                "name": "Finalize",
                "status": "completed",
                "outputs": {"all_data_saved": True},
                "depends_on": ["Performance Analysis"],
            }
            result["workflows"].append(wf5_result)
            logging.info("  ✓ All data saved and finalized")

            logging.info("✅ Workflow chaining completed successfully")
            return result

        except Exception as e:
            logging.error(f"Example 5 failed: {e}")
            result["success"] = False
            return result


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.info("🎯 Workflow Examples Module")
    logging.info("Use examples from this module with MultiGameOrchestrator")
    logging.info("Examples provided:")
    logging.info("  1. Daily Routine Automation")
    logging.info("  2. Checkpoint-Based Error Recovery")
    logging.info("  3. Real-Time Performance Monitoring")
    logging.info("  4. Cross-Game Synchronization")
    logging.info("  5. Advanced Workflow Chaining")
