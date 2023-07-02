from django import template


def month_format(month):
    return '{:02d}'.format(month)


def total_days_per_job(record):
    return sum([shift.days for shift in record.shifts.all()])


def total_days_per_month(report):
    return sum([shift.days for record in report.jobs.all() for shift in record.shifts.all()])


def worker_days(record, worker):
    worker_days = {shift.worker: shift.days for shift in record.shifts.all()}
    return worker_days.get(worker)


register = template.Library()

register.filter('month_format', month_format)
register.filter('total_days_per_job', total_days_per_job)
register.filter('total_days_per_month', total_days_per_month)
register.filter('worker_days', worker_days)
