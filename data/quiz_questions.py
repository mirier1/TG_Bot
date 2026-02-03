# Уровни сложности: 'easy', 'medium', 'hard'
# Возрастные группы: 'young', 'teen', 'student' (как в User.age_group)

QUIZ_QUESTIONS = {
    1: {  # ЦУР 1
        'young': {
            'easy': [
                {
                    "question": "Вопрос для young, сложность easy (1)",
                    "options": ["1", "2", "3"],
                    "correct": 0,
                    "explanation": "Ответ 1"
                },
                # другие вопросы
            ],
            'medium': [
                {
                    "question": "Вопрос для young, сложность medium(2)",
                    "options": ["1", "2", "3"],
                    "correct": 1,
                    "explanation": "Ответ 2"
                },
                # другие вопросы
            ],
            'hard': [
                {
                    "question": "Вопрос для young, сложность hard (3)",
                    "options": ["1", "2", "3"],
                    "correct": 2,
                    "explanation": "Ответ 3"
                },
                # другие вопросы
            ]
        },
        'teen': {
            'easy': [
                {
                    "question": "Вопрос для teen, сложность easy (1)",
                    "options": ["1", "2", "3"],
                    "correct": 0,
                    "explanation": "Ответ 1"
                },
                # другие вопросы
            ],
            'medium': [
                {
                    "question": "Вопрос для teen, сложность medium(2)",
                    "options": ["1", "2", "3"],
                    "correct": 1,
                    "explanation": "Ответ 2"
                },
                # другие вопросы
            ],
            'hard': [
                {
                    "question": "Вопрос для teen, сложность hard (3)",
                    "options": ["1", "2", "3"],
                    "correct": 2,
                    "explanation": "Ответ 3"
                },
                # другие вопросы
            ]
        },
        'student': {
            'easy': [
                {
                    "question": "Вопрос для student, сложность easy (1)",
                    "options": ["1", "2", "3"],
                    "correct": 0,
                    "explanation": "Ответ 1"
                },
                # другие вопросы
            ],
            'medium': [
                {
                    "question": "Вопрос для student, сложность medium(2)",
                    "options": ["1", "2", "3"],
                    "correct": 1,
                    "explanation": "Ответ 2"
                },
                # другие вопросы
            ],
            'hard': [
                {
                    "question": "Вопрос для student, сложность hard (3)",
                    "options": ["1", "2", "3"],
                    "correct": 2,
                    "explanation": "Ответ 3"
                },
                # другие вопросы
            ]
        }
    },
    # другие ЦУР...
}