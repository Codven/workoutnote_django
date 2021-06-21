from typing import Tuple
from datetime import date, timedelta


class Tools:
    AGE_RANGES = {
        '14-17': (14, 17),
        '18-23': (18, 23),
        '24-39': (24, 39),
        '40-49': (40, 49),
        '50-59': (50, 59),
        '60-69': (60, 69),
        '70-79': (70, 79),
        '80-89': (80, 89)
    }

    @staticmethod
    def calculate_one_rep_max(lift_mass: float, repetitions: int) -> float:
        return round(lift_mass / (1.0278 - 0.0278 * repetitions), 1)

    @staticmethod
    def get_level_in_percentage(sorted_lifts_for_body_weight: list,
                                total_lift_mass: float) -> float:
        list_copy = sorted_lifts_for_body_weight[:]
        data_length = len(list_copy)
        list_copy.append(total_lift_mass)
        list_copy.sort()
        return (list_copy.index(total_lift_mass)) / data_length * 100

    @staticmethod
    def get_level_boundaries_for_bodyweight(sorted_lifts_for_body_weight: list) -> dict:
        return {
            'beginner': sorted_lifts_for_body_weight[int(0.05 * len(sorted_lifts_for_body_weight))],
            'novice': sorted_lifts_for_body_weight[int(0.2 * len(sorted_lifts_for_body_weight))],
            'intermediate': sorted_lifts_for_body_weight[int(0.5 * len(sorted_lifts_for_body_weight))],
            'advanced': sorted_lifts_for_body_weight[int(0.8 * len(sorted_lifts_for_body_weight))],
            'elite': sorted_lifts_for_body_weight[int(0.95 * len(sorted_lifts_for_body_weight))]
        }

    @staticmethod
    def get_string_level(boundaries: dict, total_lift_mass: float) -> str:
        level = 'Beginner'  # let the default be a Beginner level
        if total_lift_mass > boundaries['beginner']:
            level = 'Beginner'
        if total_lift_mass > boundaries['beginner']:
            level = 'Novice'
        if total_lift_mass > boundaries['novice']:
            level = 'Novice'
        if total_lift_mass > boundaries['intermediate']:
            level = 'Intermediate'
        if total_lift_mass > boundaries['advanced']:
            level = 'Advanced'
        return level

    @staticmethod
    def calculate_wilks_score(total_lift_mass: float):
        # TODO: make a calculation formula
        pass

    @staticmethod
    def get_wilks_score_boundaries():
        # TODO: make a logic for finding boundaries
        pass

    @staticmethod
    def calculate_body_weight_ratio(lift_mass: float, body_weight: float):
        return lift_mass / body_weight

    @staticmethod
    def get_age_range(avg_age: float) -> Tuple[int, int]:
        for key, value in Tools.AGE_RANGES.items():
            if avg_age >= value[0] and avg_age <= value[1]:
                return value

    @staticmethod
    def get_date_of_birth_range(age_range: Tuple[int, int]) -> Tuple[date, date]:
        today = date.today()
        start_date = (today - timedelta(days=365 * age_range[0])).replace(month=1, day=1)
        end_date = (today - timedelta(days=365 * age_range[1])).replace(month=1, day=1)
        return (start_date, end_date)
