import re
from datetime import datetime
from random import randint
from docxtpl import DocxTemplate
import os

from linguistics import decline, sum_in_words
from reports.models import Settings
from django.conf import settings


RAW_ACT = 'act.docx'
RAW_INVOICE = 'invoice.docx'


def num_to_word(number: int):

    months_verbose = {
        1: 'январь',
        2: 'февраль',
        3: 'март',
        4: 'апрель',
        5: 'май',
        6: 'июнь',
        7: 'июль',
        8: 'август',
        9: 'сентябрь',
        10: 'октябрь',
        11: 'ноябрь',
        12: 'декабрь'
    }

    return months_verbose[number]


def format_number(number: int):
    """Puts a space after every 3 digits"""

    regex = r'(\d)(?=(\d{3})+(?!\d))'
    return re.sub(regex, r'\1 ', str(number))


def make_invoice(
    man_days: int,
    target_month: int,
    target_year: str = datetime.now().strftime('%Y'),     # yyyy
    stake: int = 0,
    date: str = datetime.now().strftime('%d.%m.%Y'),      # dd.mm.yyyy
    serial: str = (
        f"{datetime.now().strftime('%m').zfill(2)}{str(randint(1000,9999))}"
    )
):
    month = num_to_word(target_month)

    doc = DocxTemplate(RAW_INVOICE)

    context = {
        'invoice_number': serial,
        'date': date,
        'month_prepositional': decline(month, 'prepositional'),
        'year': target_year,
        'cost': format_number(stake),
        'man_days': str(man_days),
        'sum': format_number(man_days * stake),
        'sum_in_words': sum_in_words(man_days * stake)
    }

    doc.render(context)
    path = os.path.join(settings.BASE_DIR, 'DOCS', f"Счёт №{serial} от {date}.docx")
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    doc.save(path)

    return path


def make_act(
    man_days: int,
    report: str,
    target_month: int,
    target_year: str = datetime.now().strftime('%Y'),     # yyyy
    stake: int = 0,
    date: str = datetime.now().strftime('%d.%m.%Y'),      # dd.mm.yyyy
):
    month = num_to_word(target_month)

    doc = DocxTemplate(RAW_ACT)

    context = {
        'date': date,
        'month_genitive': decline(month, 'genitive'),
        'year': target_year,
        'month_prepositional': decline(month, 'prepositional'),
        'sum': format_number(man_days * stake),
        'sum_in_words': sum_in_words(man_days * stake),
        'report': report,
        'man_days': str(man_days)
    }

    doc.render(context)
    path = os.path.join(settings.BASE_DIR, 'DOCS', f"Акт {month}.docx")
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    doc.save(path)

    return path
