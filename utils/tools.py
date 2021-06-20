class Tools:
    @staticmethod
    def calculate_one_rep_max(lift_mass: float, repetitions: int) -> float:
        return round(lift_mass / (1.0278 - 0.0278 * repetitions), 1)

    @staticmethod
    def get_power_level_in_percentage(sorted_lifts_for_body_weight: list,
                                      total_lift_mass: float) -> float:
        data_length = len(sorted_lifts_for_body_weight)
        sorted_lifts_for_body_weight.append(total_lift_mass)
        sorted_lifts_for_body_weight.sort()
        return (sorted_lifts_for_body_weight.index(total_lift_mass) + 1) / (data_length + 1) * 100

    @staticmethod
    def get_string_power_level(level_in_percentage: float) -> str:
        level = 'Beginner'
        if level_in_percentage > 20 and level_in_percentage < 50:
            level = 'Novice'
        elif level_in_percentage > 50 and level_in_percentage < 80:
            level = 'Intermediate'
        elif level_in_percentage > 80 and level_in_percentage < 95:
            level = 'Advanced'
        elif level_in_percentage > 95:
            level = 'Elite'
        return level

    @staticmethod
    def get_level_boundaries_for_bodyweight(sorted_lifts_for_body_weight: list) -> dict:
        return {
            'beginner': sorted_lifts_for_body_weight[int(0.05 * len(sorted_lifts_for_body_weight) - 1)],
            'novice': sorted_lifts_for_body_weight[int(0.2 * len(sorted_lifts_for_body_weight) - 1)],
            'intermediate': sorted_lifts_for_body_weight[int(0.5 * len(sorted_lifts_for_body_weight) - 1)],
            'advanced': sorted_lifts_for_body_weight[int(0.8 * len(sorted_lifts_for_body_weight) - 1)],
            'elite': sorted_lifts_for_body_weight[int(0.95 * len(sorted_lifts_for_body_weight) - 1)]
        }
