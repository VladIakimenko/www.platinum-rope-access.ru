def decline(target, case):
    MONTHS = {
            'январь': {'genitive': 'января', 'prepositional': 'январе'},
            'февраль': {'genitive': 'февраля', 'prepositional': 'феврале'},
            'март': {'genitive': 'марта', 'prepositional': 'марте'},
            'апрель': {'genitive': 'апреля', 'prepositional': 'апреле'},
            'май': {'genitive': 'мая', 'prepositional': 'мае'},
            'июнь': {'genitive': 'июня', 'prepositional': 'июне'},
            'июль': {'genitive': 'июля', 'prepositional': 'июле'},
            'август': {'genitive': 'августа', 'prepositional': 'августе'},
            'сентябрь': {'genitive': 'сентября', 'prepositional': 'сентябре'},
            'октябрь': {'genitive': 'октября', 'prepositional': 'октябре'},
            'ноябрь': {'genitive': 'ноября', 'prepositional': 'ноябре'},
            'декабрь': {'genitive': 'декабря', 'prepositional': 'декабре'},
    }

    dicts = [MONTHS]

    for dictionary in dicts:
        for word in dictionary:
            if word == target.casefold().strip():
                return dictionary[word][case]

    raise ValueError('The "decline" function dictionaries do not contain the word "{target}" in "{case}" case!')

 

def sum_in_words(sum_):
    units_verbose = ['', "один", "два", "три", "четыре", "пять", "шесть", "семь", "восемь", "девять"]
    tens_verbose = [
        '',
        ["", "одинадцать", "двенадцать", "тринадцать", "четырнадцать", "пятнадцать", "шестнадцать", "семнадцать", "восемнадцать", "девятнадцать"],
        "двадцать",
        "тридцать",
        "сорок",
        "пятьдесят",
        "шестьдесят",
        "семьдесят",
        "восемьдесят",
        "девяносто"
    ]
    hundreds_verbose = ['', "сто", "двести", "триста", "четыреста", "пятьсот", "шестьсот", "семьсот", "восемьсот", "девятьсот"]

    units = sum_ % 10
    tens = sum_ % 100 // 10
    hundreds = sum_ % 1000 // 100
    
    thousands = sum_ // 1000
    thousands_units = thousands % 10
    thousands_tens = thousands % 100 // 10
    thousands_hundreds = thousands % 1000 // 100

    word_thousand = 'тысяч'
    if thousands_units < 5:
        if thousands_tens != 1:
            word_thousand += ("и", "а")[thousands_units == 1]

    def adopt_gender(word):
        dictionary = {
            "один": "одна",
            "два": "две"
        }
        return dictionary[word] if word in dictionary else word

    return ''.join([
        f'{hundreds_verbose[thousands_hundreds]} ',
        f'{tens_verbose[thousands_tens]} ' if thousands_tens != 1 else tens_verbose[thousands_tens][thousands_units],
        f'{adopt_gender(units_verbose[thousands_units])} ' if thousands_tens != 1 else ' ',
        f'{word_thousand} ' if thousands else '',
        f'{hundreds_verbose[hundreds]} ',
        f'{tens_verbose[tens]} ' if tens != 1 else tens_verbose[tens][units],
        f'{units_verbose[units]}' if tens != 1 else ''
    ]).strip()


