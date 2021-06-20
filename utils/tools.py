class Tools:
    @staticmethod
    def calculate_one_rep_max(lift_mass: float, repetitions: int) -> float:
        return round(lift_mass / (1.0278 - 0.0278 * repetitions), 1)

    @staticmethod
    def get_power_level_in_percentage(sorted_lifts_for_body_weight: list,
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
