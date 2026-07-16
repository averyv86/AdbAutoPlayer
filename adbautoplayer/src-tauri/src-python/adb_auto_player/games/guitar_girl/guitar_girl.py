import logging
from time import sleep, time
from typing import NoReturn, Optional
from collections import deque

from adb_auto_player.decorators import register_command, register_game
from adb_auto_player.game import Game
from adb_auto_player.models import ConfidenceValue
from adb_auto_player.models.decorators import GUIMetadata
from adb_auto_player.models.device import Resolution
from adb_auto_player.models.geometry import Point
from adb_auto_player.models.image_manipulation import CropRegions
from adb_auto_player.util import SummaryGenerator

from .yolo_classes import YOLO_CLASSES, get_all_templates


@register_game(
    name="Guitar Girl",
)
class GuitarGirl(Game):
    def __init__(self) -> None:
        """Initialize GuitarGirl with timing and state tracking."""
        super().__init__()
        self.base_resolution: Resolution = Resolution.from_string("1080x1920")
        self.package_name_prefixes = ["com.neowiz.game.guitargirl"]

        # Timing tracking for rhythm detection
        self.tap_history: deque = deque(maxlen=100)  # Last 100 taps
        self.last_tap_time: float = 0
        self.note_detection_stats = {
            "small_notes": 0,
            "big_notes": 0,
            "big_notes2": 0,
            "hold_notes": 0,
            "double_notes": 0,
            "misses": 0,
        }

    @property
    def settings(self):
        raise RuntimeError("Not Implemented")

    def _detect_notes_with_timing(self) -> Optional[tuple]:
        """Detect notes using template matching with timing awareness.

        Returns:
            Tuple of (template_match_result, note_type) or None if no note found
        """
        # Try all available templates with confidence thresholds
        for note_class in YOLO_CLASSES.values():
            if result := self.find_any_template(
                templates=[note_class.template_fallback],
                threshold=ConfidenceValue(f"{int(note_class.confidence_threshold * 100)}%"),
                crop_regions=CropRegions(bottom=0.5, right=0.2, top=0.05),
            ):
                self.note_detection_stats[note_class.name] += 1
                self.last_tap_time = time()
                self.tap_history.append((self.last_tap_time, note_class.name))
                return (result, note_class.name)

        self.note_detection_stats["misses"] += 1
        return None

    def _tap_with_timing(self, result, log: bool = False) -> None:
        """Tap on note with timing tracking.

        Args:
            result: Template match result to tap on
            log: Whether to log the tap
        """
        current_time = time()
        self.tap(result, log=log)
        self.last_tap_time = current_time
        self.tap_history.append((current_time, "tap"))

    def _get_tap_rhythm_analysis(self) -> dict:
        """Analyze tap rhythm from history.

        Returns:
            Dictionary with rhythm statistics
        """
        if len(self.tap_history) < 2:
            return {"avg_interval": 0, "consistency": 0}

        intervals = []
        for i in range(1, len(self.tap_history)):
            interval = self.tap_history[i][0] - self.tap_history[i - 1][0]
            if interval > 0.01:  # Filter out rapid double taps
                intervals.append(interval)

        if not intervals:
            return {"avg_interval": 0, "consistency": 0}

        avg_interval = sum(intervals) / len(intervals)
        variance = sum((x - avg_interval) ** 2 for x in intervals) / len(intervals)
        consistency = max(0, 100 - (variance * 100))  # Higher is better

        return {"avg_interval": avg_interval, "consistency": consistency}

    @register_command(gui=GUIMetadata(label="Busk"))
    def busk(self) -> NoReturn:
        """Enhanced busk automation with timing-aware note detection.

        Uses timing analysis to track performance and adapt detection sensitivity.
        """
        self.open_eyes(device_streaming=False)
        counter = 0
        mod = 3000
        logging.info("Starting enhanced busk automation with timing tracking.")

        while True:
            if counter == (mod - 1):
                self._start_game_if_not_running()
                rhythm = self._get_tap_rhythm_analysis()
                logging.info(f"Rhythm analysis: {rhythm}")

            if counter == 0:
                sleep(3)
                self._check_for_popups()
                self._level_up_guitar_girl()
                self._level_up_classmate_joy()
                self._activate_skills()
                logging.info("Tapping Music Notes (Enhanced with timing awareness).")

            # Use enhanced timing-aware note detection
            if detection := self._detect_notes_with_timing():
                result, note_type = detection
                self._tap_with_timing(result, log=False)

                # Log statistics
                if "big_note" in note_type:
                    SummaryGenerator.increment("Guitar Girl", "Big Notes clicked")
                    logging.debug(f"Detected {note_type} (confidence: {result.confidence}%)")
                else:
                    SummaryGenerator.increment("Guitar Girl", "Small Notes clicked")

            counter += 1
            counter = counter % mod
        # No Return

    @register_command(gui=GUIMetadata(label="Play"))
    def play(self) -> NoReturn:
        self.open_eyes(device_streaming=True)
        counter = 0
        y = 200
        y_max = 960
        mod = 10000
        while True:
            if counter == (mod - 1):
                self._start_game_if_not_running()

            if counter == 0:
                sleep(3)
                self._check_for_popups()
                self._level_up_guitar_girl()
                self._activate_skills()
                logging.info("Tapping.")

            self.tap(Point(500, y), log=False)
            y += 40
            if y > y_max:
                y = 200

            counter += 1
            counter = counter % mod
        # NoReturn

    def _level_up_guitar_girl(self) -> None:
        logging.info("Leveling up Guitar Girl.")
        self._open_guitar_girl_tab()

        guitar_girl_level_up = Point(900, 1450)
        for _ in range(50):
            self.tap(guitar_girl_level_up, log=False)
        sleep(3)

        guitar_girl_icon = Point(100, 1450)
        for _ in range(3):
            self.tap(guitar_girl_icon, log=False)
        sleep(1)

    def _level_up_classmate_joy(self) -> None:
        logging.info("Leveling up Classmate Joy.")
        self._open_follower_tab()

        classmate_joy_level_up = Point(900, 1250)
        for _ in range(50):
            self.tap(classmate_joy_level_up, log=False)
        sleep(3)

        classmate_joy_icon = Point(100, 1250)
        for _ in range(3):
            self.tap(classmate_joy_icon, log=False)
        sleep(1)

    def _activate_skills(self) -> None:
        logging.info("Activating Skills.")
        self._open_guitar_girl_tab()

        base_x = 200
        y = 1280
        x_offset = 230
        num_skills = 3

        for i in range(num_skills):
            x = base_x + i * x_offset
            self.tap(Point(x, y), log=False)
            sleep(1)

    def _start_game_if_not_running(self) -> None:
        if not self.is_game_running():
            logging.warning("Restarting Guitar Girl.")
            self.start_game()
            sleep(15)

    def _open_guitar_girl_tab(self) -> None:
        self.tap(Point(80, 1850), log=False)
        sleep(1)

    def _open_follower_tab(self):
        self.tap(Point(210, 1850), log=False)
        sleep(1)

    def _check_for_popups(self) -> None:
        logging.info("Checking for popups.")
        while result := self.find_any_template(
            ["close.png", "ok.png"],
        ):
            self._tap_coordinates_till_template_disappears(
                coordinates=result,
                template=result.template,
            )
            sleep(5)
