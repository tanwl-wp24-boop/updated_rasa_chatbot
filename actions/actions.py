from pathlib import Path
import csv
from typing import Any, Dict, List, Optional, Text, Tuple

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import AllSlotsReset, SlotSet
from rasa_sdk.forms import FormValidationAction


# =========================================================
# DATASET LOCATION
# =========================================================

DATASET_PATH = (
    Path(__file__).resolve().parents[1]
    / "dataset"
    / "megaGymDataset.csv"
)

_EXERCISES: Optional[List[Dict[str, str]]] = None


# =========================================================
# VALID DATASET VALUES
# =========================================================

BODY_PARTS = [
    "Abdominals",
    "Abductors",
    "Adductors",
    "Biceps",
    "Calves",
    "Chest",
    "Forearms",
    "Glutes",
    "Hamstrings",
    "Lats",
    "Lower Back",
    "Middle Back",
    "Neck",
    "Quadriceps",
    "Shoulders",
    "Traps",
    "Triceps",
]

EQUIPMENT_TYPES = [
    "Bands",
    "Barbell",
    "Body Only",
    "Cable",
    "Dumbbell",
    "E-Z Curl Bar",
    "Exercise Ball",
    "Foam Roll",
    "Kettlebells",
    "Machine",
    "Medicine Ball",
    "Other",
]

EXPERIENCE_LEVELS = [
    "Beginner",
    "Intermediate",
    "Expert",
]

EXERCISE_TYPES = [
    "Cardio",
    "Olympic Weightlifting",
    "Plyometrics",
    "Powerlifting",
    "Strength",
    "Stretching",
    "Strongman",
]


# =========================================================
# BODY-PART GROUPS
# These allow general requests such as "legs" and "back".
# =========================================================

BODY_PART_GROUPS = {
    "leg": [
        "Quadriceps",
        "Hamstrings",
        "Glutes",
        "Calves",
        "Adductors",
        "Abductors",
    ],
    "arms": [
        "Biceps",
        "Triceps",
        "Forearms",
    ],
    "back": [
        "Lats",
        "Middle Back",
        "Lower Back",
        "Traps",
    ],
    "upper body": [
        "Chest",
        "Shoulders",
        "Biceps",
        "Triceps",
        "Forearms",
        "Lats",
        "Middle Back",
        "Traps",
        "Abdominals",
    ],
    "full body": BODY_PARTS,
}


# =========================================================
# USER-WORDING ALIASES
# =========================================================

BODY_PART_ALIASES = {
    "abs": "Abdominals",
    "ab": "Abdominals",
    "abdominal": "Abdominals",
    "abdominals": "Abdominals",
    "stomach": "Abdominals",
    "core": "Abdominals",

    "bicep": "Biceps",
    "tricep": "Triceps",
    "forearm": "Forearms",
    "shoulder": "Shoulders",
    "trap": "Traps",
    "lat": "Lats",
    "calf": "Calves",
    "glute": "Glutes",
    "hamstring": "Hamstrings",
    "quad": "Quadriceps",
    "quads": "Quadriceps",

    "lowerback": "Lower Back",
    "lower back": "Lower Back",
    "middleback": "Middle Back",
    "middle back": "Middle Back",

    "leg": "leg",
    "legs": "leg",
    "leg day": "leg",
    "lower body": "leg",

    "arm": "arms",
    "arms": "arms",
    "arm day": "arms",

    "back": "back",
    "back day": "back",
    "upper back": "back",

    "upper body": "upper body",
    "full body": "full body",
    "whole body": "full body",
}

EQUIPMENT_ALIASES = {
    "band": "Bands",
    "bands": "Bands",
    "resistance band": "Bands",
    "resistance bands": "Bands",
    "exercise band": "Bands",

    "bodyweight": "Body Only",
    "body weight": "Body Only",
    "body only": "Body Only",
    "no equipment": "Body Only",
    "without equipment": "Body Only",

    "dumbbells": "Dumbbell",
    "barbells": "Barbell",
    "cables": "Cable",

    "kettlebell": "Kettlebells",
    "kettle bell": "Kettlebells",
    "kettle bells": "Kettlebells",

    "machine": "Machine",
    "machines": "Machine",

    "medicine ball": "Medicine Ball",
    "exercise ball": "Exercise Ball",
    "stability ball": "Exercise Ball",

    "ez curl bar": "E-Z Curl Bar",
    "e-z curl bar": "E-Z Curl Bar",
    "foam roller": "Foam Roll",
}

LEVEL_ALIASES = {
    "beginner": "Beginner",
    "beginner level": "Beginner",
    "newbie": "Beginner",
    "new": "Beginner",
    "easy": "Beginner",
    "new to the gym": "Beginner",

    "intermediate": "Intermediate",
    "medium": "Intermediate",
    "moderate": "Intermediate",
    "normal": "Intermediate",

    "expert": "Expert",
    "advanced": "Expert",
    "professional": "Expert",
    "difficult": "Expert",
}

EXERCISE_TYPE_ALIASES = {
    "cardio": "Cardio",
    "cardiovascular": "Cardio",

    "strength": "Strength",
    "strength training": "Strength",
    "weight training": "Strength",

    "stretch": "Stretching",
    "stretching": "Stretching",
    "flexibility": "Stretching",

    "plyometric": "Plyometrics",
    "plyometrics": "Plyometrics",

    "powerlifting": "Powerlifting",

    "olympic lifting": "Olympic Weightlifting",
    "olympic weightlifting": "Olympic Weightlifting",

    "strongman": "Strongman",
}


# =========================================================
# GENERAL HELPER FUNCTIONS
# =========================================================

def clean_text(value: Any) -> str:
    """Return a clean string and safely handle missing values."""
    if value is None:
        return ""

    text = str(value).strip()

    if text.casefold() in {"nan", "none", "null"}:
        return ""

    return text


def canonical_value(
    value: Optional[str],
    valid_values: List[str],
) -> Optional[str]:
    """Match a value to a dataset category, ignoring case."""
    if not value:
        return None

    cleaned = clean_text(value)

    for valid_value in valid_values:
        if cleaned.casefold() == valid_value.casefold():
            return valid_value

    return None


def normalise_body_part(
    value: Optional[str],
) -> Optional[str]:
    """Convert user wording into a body part or body-part group."""
    if not value:
        return None

    cleaned = clean_text(value)
    key = cleaned.casefold()

    if key in BODY_PART_ALIASES:
        return BODY_PART_ALIASES[key]

    return canonical_value(cleaned, BODY_PARTS)


def normalise_equipment(
    value: Optional[str],
) -> Optional[str]:
    """Convert user wording into a dataset equipment value."""
    if not value:
        return None

    cleaned = clean_text(value)
    key = cleaned.casefold()

    if key in EQUIPMENT_ALIASES:
        return EQUIPMENT_ALIASES[key]

    return canonical_value(cleaned, EQUIPMENT_TYPES)


def normalise_level(
    value: Optional[str],
) -> Optional[str]:
    """Convert user wording into a dataset difficulty level."""
    if not value:
        return None

    cleaned = clean_text(value)
    key = cleaned.casefold()

    if key in LEVEL_ALIASES:
        return LEVEL_ALIASES[key]

    return canonical_value(cleaned, EXPERIENCE_LEVELS)


def normalise_exercise_type(
    value: Optional[str],
) -> Optional[str]:
    """Convert user wording into a dataset exercise type."""
    if not value:
        return None

    cleaned = clean_text(value)
    key = cleaned.casefold()

    if key in EXERCISE_TYPE_ALIASES:
        return EXERCISE_TYPE_ALIASES[key]

    return canonical_value(cleaned, EXERCISE_TYPES)


def get_body_part_targets(body_part: str) -> List[str]:
    """Return all dataset body parts represented by a user request."""
    if body_part in BODY_PART_GROUPS:
        return BODY_PART_GROUPS[body_part]

    return [body_part]


# =========================================================
# DATASET FUNCTIONS
# =========================================================

def load_exercises() -> List[Dict[str, str]]:
    """Load the CSV once and keep it in memory."""
    global _EXERCISES

    if _EXERCISES is not None:
        return _EXERCISES

    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Exercise dataset not found at: {DATASET_PATH}"
        )

    loaded_exercises: List[Dict[str, str]] = []

    with DATASET_PATH.open(
        mode="r",
        encoding="utf-8-sig",
        newline="",
    ) as csv_file:

        reader = csv.DictReader(csv_file)

        for row in reader:
            cleaned_row = {
                key: clean_text(value)
                for key, value in row.items()
                if key is not None
            }

            if cleaned_row.get("Title"):
                loaded_exercises.append(cleaned_row)

    _EXERCISES = loaded_exercises
    return _EXERCISES


def get_rating(exercise: Dict[str, str]) -> float:
    """Return an exercise's rating or -1 when no rating exists."""
    rating_text = clean_text(exercise.get("Rating"))

    if not rating_text:
        return -1.0

    try:
        return float(rating_text)
    except ValueError:
        return -1.0


def filter_exercises(
    exercises: List[Dict[str, str]],
    body_part: str,
    level: Optional[str],
    equipment: Optional[str],
    exercise_type: Optional[str],
) -> List[Dict[str, str]]:
    """Filter exercises using the selected preferences."""
    target_body_parts = {
        item.casefold()
        for item in get_body_part_targets(body_part)
    }

    matches = [
        exercise
        for exercise in exercises
        if clean_text(
            exercise.get("BodyPart")
        ).casefold() in target_body_parts
    ]

    if level:
        matches = [
            exercise
            for exercise in matches
            if clean_text(
                exercise.get("Level")
            ).casefold() == level.casefold()
        ]

    if equipment:
        matches = [
            exercise
            for exercise in matches
            if clean_text(
                exercise.get("Equipment")
            ).casefold() == equipment.casefold()
        ]

    if exercise_type:
        matches = [
            exercise
            for exercise in matches
            if clean_text(
                exercise.get("Type")
            ).casefold() == exercise_type.casefold()
        ]

    return matches


def rank_exercises(
    exercises: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    """Prioritise rated exercises with useful descriptions."""
    return sorted(
        exercises,
        key=lambda exercise: (
            get_rating(exercise),
            bool(clean_text(exercise.get("Desc"))),
            clean_text(exercise.get("Title")).casefold(),
        ),
        reverse=True,
    )


def select_diverse_exercises(
    exercises: List[Dict[str, str]],
    limit: int = 3,
) -> List[Dict[str, str]]:
    """
    Select high-quality exercises while adding body-part variety
    for grouped requests such as legs or upper body.
    """
    ranked = rank_exercises(exercises)

    selected: List[Dict[str, str]] = []
    used_body_parts = set()
    used_titles = set()

    # First choose exercises from different body parts.
    for exercise in ranked:
        body_part = clean_text(exercise.get("BodyPart")).casefold()
        title = clean_text(exercise.get("Title")).casefold()

        if title in used_titles:
            continue

        if body_part not in used_body_parts:
            selected.append(exercise)
            used_body_parts.add(body_part)
            used_titles.add(title)

        if len(selected) >= limit:
            return selected

    # Fill remaining spaces with the next best exercises.
    for exercise in ranked:
        title = clean_text(exercise.get("Title")).casefold()

        if title in used_titles:
            continue

        selected.append(exercise)
        used_titles.add(title)

        if len(selected) >= limit:
            break

    return selected


def find_best_matches(
    exercises: List[Dict[str, str]],
    body_part: str,
    level: Optional[str],
    equipment: Optional[str],
    exercise_type: Optional[str],
) -> Tuple[List[Dict[str, str]], List[str]]:
    """
    Try an exact search first.

    When no result exists, relax filters in this order:
    1. Exercise type
    2. Experience level
    3. Equipment

    The body-part requirement is never removed.
    """
    attempts = [
        (
            level,
            equipment,
            exercise_type,
        )
    ]

    if exercise_type:
        attempts.append(
            (
                level,
                equipment,
                None,
            )
        )

    if level:
        attempts.append(
            (
                None,
                equipment,
                None,
            )
        )

    if equipment:
        attempts.append(
            (
                level,
                None,
                None,
            )
        )

    attempts.append(
        (
            None,
            None,
            None,
        )
    )

    unique_attempts = []

    for attempt in attempts:
        if attempt not in unique_attempts:
            unique_attempts.append(attempt)

    for attempt_level, attempt_equipment, attempt_type in unique_attempts:
        matches = filter_exercises(
            exercises=exercises,
            body_part=body_part,
            level=attempt_level,
            equipment=attempt_equipment,
            exercise_type=attempt_type,
        )

        if matches:
            relaxed_filters = []

            if (
                exercise_type
                and attempt_type is None
            ):
                relaxed_filters.append(
                    f"exercise type '{exercise_type}'"
                )

            if (
                level
                and attempt_level is None
            ):
                relaxed_filters.append(
                    f"level '{level}'"
                )

            if (
                equipment
                and attempt_equipment is None
            ):
                relaxed_filters.append(
                    f"equipment '{equipment}'"
                )

            return matches, relaxed_filters

    return [], []


# =========================================================
# FORM SLOT VALIDATION
# =========================================================

class ValidateExerciseForm(FormValidationAction):

    def name(self) -> Text:
        return "validate_exercise_form"

    async def validate_body_part(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:

        body_part = normalise_body_part(
            clean_text(slot_value)
        )

        if body_part:
            return {
                "body_part": body_part
            }

        dispatcher.utter_message(
            text=(
                "I could not recognise that body part. "
                "Try chest, back, shoulders, arms, abs, "
                "legs, glutes, hamstrings, or quadriceps."
            )
        )

        return {
            "body_part": None
        }

    async def validate_level(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:

        level = normalise_level(
            clean_text(slot_value)
        )

        if level:
            return {
                "level": level
            }

        dispatcher.utter_message(
            text=(
                "Please choose one of these experience levels: "
                "beginner, intermediate, or expert."
            )
        )

        return {
            "level": None
        }

    async def validate_equipment(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:

        equipment = normalise_equipment(
            clean_text(slot_value)
        )

        if equipment:
            return {
                "equipment": equipment
            }

        return {
            "equipment": None
        }

    async def validate_exercise_type(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:

        exercise_type = normalise_exercise_type(
            clean_text(slot_value)
        )

        if exercise_type:
            return {
                "exercise_type": exercise_type
            }

        return {
            "exercise_type": None
        }


# =========================================================
# EXERCISE RECOMMENDATION ACTION
# =========================================================

class ActionRecommendExercise(Action):

    def name(self) -> Text:
        return "action_recommend_exercise"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        body_part = normalise_body_part(
            tracker.get_slot("body_part")
        )

        level = normalise_level(
            tracker.get_slot("level")
        )

        equipment = normalise_equipment(
            tracker.get_slot("equipment")
        )

        exercise_type = normalise_exercise_type(
            tracker.get_slot("exercise_type")
        )

        if not body_part:
            dispatcher.utter_message(
                text=(
                    "Please tell me which body part "
                    "you would like to train."
                )
            )
            return []

        if not level:
            dispatcher.utter_message(
                text=(
                    "Please tell me whether you are a beginner, "
                    "intermediate, or expert."
                )
            )
            return []

        try:
            exercises = load_exercises()

        except FileNotFoundError:
            dispatcher.utter_message(
                text=(
                    "I could not find megaGymDataset.csv. "
                    "Make sure it is inside the dataset folder."
                )
            )
            return []

        except (OSError, csv.Error) as error:
            print(
                f"Unable to read exercise dataset: {error}"
            )

            dispatcher.utter_message(
                text=(
                    "I encountered a problem while reading "
                    "the exercise dataset."
                )
            )
            return []

        matches, relaxed_filters = find_best_matches(
            exercises=exercises,
            body_part=body_part,
            level=level,
            equipment=equipment,
            exercise_type=exercise_type,
        )

        if not matches:
            dispatcher.utter_message(
                text=(
                    "I could not find any exercise for that "
                    "body-part selection. Try another body part."
                )
            )
            return []

        recommendations = select_diverse_exercises(
            matches,
            limit=3,
        )

        criteria = [
            f"target: {body_part}",
            f"level: {level}",
        ]

        if equipment:
            criteria.append(
                f"equipment: {equipment}"
            )

        if exercise_type:
            criteria.append(
                f"type: {exercise_type}"
            )

        response_lines = [
            (
                f"I searched using {', '.join(criteria)}."
            )
        ]

        if relaxed_filters:
            response_lines.append(
                (
                    "No exact match was available, so I relaxed: "
                    + ", ".join(relaxed_filters)
                    + "."
                )
            )

        response_lines.append(
            (
                f"I found {len(matches)} suitable result(s). "
                "Here are the top recommendations:"
            )
        )

        for number, exercise in enumerate(
            recommendations,
            start=1,
        ):
            title = clean_text(
                exercise.get("Title")
            ) or "Unnamed exercise"

            result_type = clean_text(
                exercise.get("Type")
            ) or "Not specified"

            result_body_part = clean_text(
                exercise.get("BodyPart")
            ) or "Not specified"

            result_equipment = clean_text(
                exercise.get("Equipment")
            ) or "Not specified"

            result_level = clean_text(
                exercise.get("Level")
            ) or "Not specified"

            rating = get_rating(exercise)

            response_lines.extend(
                [
                    "",
                    f"{number}. {title}",
                    f"   Type: {result_type}",
                    f"   Body part: {result_body_part}",
                    f"   Equipment: {result_equipment}",
                    f"   Level: {result_level}",
                ]
            )

            if rating >= 0:
                response_lines.append(
                    f"   Rating: {rating:g}/10"
                )

        response_lines.extend(
            [
                "",
                (
                    "Ask me to explain the exercise for more "
                    "information about the first recommendation."
                ),
                (
                    "Use proper form and stop if you experience "
                    "sharp pain, dizziness, or unusual discomfort."
                ),
            ]
        )

        dispatcher.utter_message(
            text="\n".join(response_lines)
        )

        first_exercise = recommendations[0]

        return [
            SlotSet(
                "last_exercise_title",
                clean_text(
                    first_exercise.get("Title")
                ),
            ),
            SlotSet(
                "last_exercise_description",
                clean_text(
                    first_exercise.get("Desc")
                ),
            ),
            SlotSet(
                "last_exercise_body_part",
                clean_text(
                    first_exercise.get("BodyPart")
                ),
            ),
            SlotSet(
                "last_exercise_equipment",
                clean_text(
                    first_exercise.get("Equipment")
                ),
            ),
            SlotSet(
                "last_exercise_level",
                clean_text(
                    first_exercise.get("Level")
                ),
            ),
        ]


# =========================================================
# EXERCISE DETAILS ACTION
# =========================================================

class ActionExerciseDetails(Action):

    def name(self) -> Text:
        return "action_exercise_details"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        title = clean_text(
            tracker.get_slot("last_exercise_title")
        )

        description = clean_text(
            tracker.get_slot(
                "last_exercise_description"
            )
        )

        body_part = clean_text(
            tracker.get_slot(
                "last_exercise_body_part"
            )
        )

        equipment = clean_text(
            tracker.get_slot(
                "last_exercise_equipment"
            )
        )

        level = clean_text(
            tracker.get_slot(
                "last_exercise_level"
            )
        )

        if not title:
            dispatcher.utter_message(
                response="utter_no_previous_exercise"
            )
            return []

        response_lines = [
            f"Exercise: {title}",
            f"Target body part: {body_part or 'Not specified'}",
            f"Equipment: {equipment or 'Not specified'}",
            f"Level: {level or 'Not specified'}",
            "",
        ]

        if description:
            response_lines.append(
                f"Dataset overview: {description}"
            )
        else:
            response_lines.append(
                (
                    "The dataset does not contain a detailed "
                    "description for this exercise."
                )
            )

        response_lines.extend(
            [
                "",
                (
                    "The dataset overview may not provide complete "
                    "step-by-step form instructions. Use a qualified "
                    "trainer when you are unsure about the technique."
                ),
            ]
        )

        dispatcher.utter_message(
            text="\n".join(response_lines)
        )

        return []


# =========================================================
# RESET ACTION
# =========================================================

class ActionResetPreferences(Action):

    def name(self) -> Text:
        return "action_reset_preferences"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        return [
            AllSlotsReset()
        ]