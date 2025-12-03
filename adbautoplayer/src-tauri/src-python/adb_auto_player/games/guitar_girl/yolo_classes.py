"""YOLO class definitions for Guitar Girl note detection."""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List


class NoteType(Enum):
    """Guitar Girl note types detected by YOLO."""

    SMALL_NOTE = "small_note"  # Regular note (70% confidence)
    BIG_NOTE = "big_note"  # Larger/stronger note (75% confidence)
    BIG_NOTE2 = "big_note2"  # Alternative big note variant (75% confidence)
    HOLD_NOTE = "hold_note"  # Long press note (80% confidence)
    DOUBLE_NOTE = "double_note"  # Two simultaneous notes (85% confidence)


@dataclass
class NoteClass:
    """YOLO class definition for a note type."""

    class_id: int
    name: str
    note_type: NoteType
    confidence_threshold: float
    template_fallback: str
    score_multiplier: float = 1.0


# YOLO Class ID Mappings (0-4)
YOLO_CLASSES: Dict[int, NoteClass] = {
    0: NoteClass(
        class_id=0,
        name="small_note",
        note_type=NoteType.SMALL_NOTE,
        confidence_threshold=0.70,
        template_fallback="note.png",
        score_multiplier=1.0,
    ),
    1: NoteClass(
        class_id=1,
        name="big_note",
        note_type=NoteType.BIG_NOTE,
        confidence_threshold=0.75,
        template_fallback="big_note.png",
        score_multiplier=1.5,
    ),
    2: NoteClass(
        class_id=2,
        name="big_note2",
        note_type=NoteType.BIG_NOTE2,
        confidence_threshold=0.75,
        template_fallback="big_note2.png",
        score_multiplier=1.5,
    ),
    3: NoteClass(
        class_id=3,
        name="hold_note",
        note_type=NoteType.HOLD_NOTE,
        confidence_threshold=0.80,
        template_fallback="hold_note.png",
        score_multiplier=2.0,
    ),
    4: NoteClass(
        class_id=4,
        name="double_note",
        note_type=NoteType.DOUBLE_NOTE,
        confidence_threshold=0.85,
        template_fallback="double_note.png",
        score_multiplier=3.0,
    ),
}


def get_class_by_id(class_id: int) -> NoteClass:
    """Get YOLO class definition by ID.

    Args:
        class_id: YOLO class ID (0-4)

    Returns:
        NoteClass definition

    Raises:
        ValueError: If class_id is not in range 0-4
    """
    if class_id not in YOLO_CLASSES:
        raise ValueError(f"Invalid YOLO class ID: {class_id}. Must be 0-4.")
    return YOLO_CLASSES[class_id]


def get_class_by_name(name: str) -> NoteClass:
    """Get YOLO class definition by name.

    Args:
        name: Class name (e.g., 'small_note', 'big_note')

    Returns:
        NoteClass definition

    Raises:
        ValueError: If name is not found
    """
    for class_def in YOLO_CLASSES.values():
        if class_def.name == name:
            return class_def
    raise ValueError(f"Unknown class name: {name}")


def get_all_templates() -> List[str]:
    """Get all template file names for fallback detection.

    Returns:
        List of template file names
    """
    return [cls.template_fallback for cls in YOLO_CLASSES.values()]


def get_confidence_threshold(class_id: int) -> float:
    """Get confidence threshold for a note class.

    Args:
        class_id: YOLO class ID

    Returns:
        Confidence threshold (0.0-1.0)
    """
    return get_class_by_id(class_id).confidence_threshold


def get_score_multiplier(class_id: int) -> float:
    """Get score multiplier for a note class.

    Args:
        class_id: YOLO class ID

    Returns:
        Score multiplier for game scoring
    """
    return get_class_by_id(class_id).score_multiplier
