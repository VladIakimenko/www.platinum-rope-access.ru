from datetime import datetime
import os

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.conf import settings
from django.http import HttpResponse
from django.core.mail import EmailMessage
from django.core.exceptions import ObjectDoesNotExist

from reports.models import Report, JobRecord, Worker, WorkerJobRecord, Settings
from reports.forms import JobRecordForm
from reports.utils import format_response
from docs import num_to_word, make_act, make_invoice
from linguistics import decline


def login_view(request):

    current_month = datetime.now().month
    current_year = datetime.now().year

    try:
        stake = Settings.load().stake
    except ObjectDoesNotExist:
        stake = os.environ.get('DEFAULT_STAKE')

    last_report = Report.objects.order_by('-year', '-month').first()

    if last_report:
        latest_year = last_report.year
        latest_month = last_report.month

        if latest_year < current_year \
            or (
                latest_year == current_year and 
                latest_month < current_month
            ):
            for year in range(latest_year, current_year + 1):
                start_month = latest_month if year == latest_year else 1
                end_month = current_month if year == current_year else 12

                for month in range(start_month, end_month + 1):
                    if not Report.objects.filter(year=year, month=month).exists():
                        Report.objects.create(year=year, month=month, stake=stake)
                    
    elif not Report.objects.filter(year=current_year, month=current_month).exists():
        Report.objects.create(year=current_year, month=current_month, stake=stake)

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect(
                'report',
                month=datetime.now().strftime('%m'),
                year=datetime.now().strftime('%Y')
              )
        else:
            return render(request, 'login.html', {
                'error': 'Неверный пароль',
                'users': User.objects.all(),
            })
    else:
        queryset = User.objects.all()

        context = {
            'users': queryset
        }

        template = 'login.html'
        return render(request, template, context)


@login_required
def report_view(request, month, year):
    report = Report.objects.get(month=month, year=year)
    job_records = JobRecord.objects.filter(report=report)
    workers = Worker.objects.all()
    error = False

    if request.method == 'POST':
        form = JobRecordForm(request.POST)
        record_id = request.POST.get('record_id')

        if record_id:
            job_record = get_object_or_404(JobRecord, id=record_id)
            form = JobRecordForm(request.POST, instance=job_record)
        else:
            form = JobRecordForm(request.POST)

        def check_for_errors():
            if (
                request.POST.get('date') and
                int(request.POST.get('date').split('-')[1]) != report.month
            ):
                return (
                    'Некорректно выбрана дата. '
                    'Выбранный Вами месяц не совпадает с отчётным.'
                )

            if not any(
                value for key, value in request.POST.items()
                if key.startswith('days_')
            ):
                return (
                    'Некорректно указано количество трудодней. '
                    'Должен быть добавлен хотя бы один день '
                    'хотя бы одному исполнителю.'
                )

            if not request.POST.get('job_description'):
                return (
                    'Не заполнено описание работ. '
                    'Это поле не может быть пустым.'
                )

            return False

        error = check_for_errors()

        if not error and form.is_valid():
            job_record = form.save()

            if not record_id:   # CREATING A NEW RECORD
                for worker in Worker.objects.all():
                    days = request.POST.get(f'days_{worker.id}')
                    kwargs = {'worker': worker, 'job_record': job_record}
                    if days:
                        kwargs['days'] = days
                        WorkerJobRecord.objects.create(**kwargs)

            else:   # UPDATING AN EXISTING RECORD
                for worker in Worker.objects.all():
                    days = request.POST.get(f'days_{worker.id}')
                    if days:

                        try:    # if days are set and record exists
                            worker_job_record = WorkerJobRecord.objects.get(
                                worker=worker,
                                job_record=job_record
                                
                            )
                            worker_job_record.days = days
                            worker_job_record.save()

                        except WorkerJobRecord.DoesNotExist:    # if days are set and there is no such record
                            worker_job_record = WorkerJobRecord.objects.create(
                                worker=worker,
                                job_record=job_record,
                                days=days
                            )
                    else:
                        try:    # if there are no days set (removed) and the record exists
                            worker_job_record = WorkerJobRecord.objects.get(
                                worker=worker,
                                job_record=job_record
                            )
                            worker_job_record.delete()
                            job_records = JobRecord.objects.filter(report=report)
                        except WorkerJobRecord.DoesNotExist:    # if there are no days set and there is no record (nothing changed)
                            pass

            return redirect('report', month=month, year=year)

    get_params = tuple(request.GET.items())
    if get_params:
        action, job_id = get_params[0][0], get_params[0][1]

        if action == 'delete':
            JobRecord.objects.get(id=job_id).delete()
            return redirect('report', month=month, year=year)

    prev_month = (
        Report.objects.filter(month__lt=month).order_by('-month').first()
    )
    next_month = (
        Report.objects.filter(month__gt=month).order_by('month').first()
    )

    template = 'report.html'

    context = {
        'report': report,
        'prev_month': prev_month if prev_month else None,
        'next_month': next_month if next_month else None,
        'job_records': job_records,
        'workers': workers,
        'form': JobRecordForm(),
        'users': request.user,
        'error': error,
    }

    return render(request, template, context)


@login_required
def send_email(request):
    report_serialized = request.POST.get('report')
    month, year = map(int, report_serialized.split('.'))
    report = Report.objects.get(month=month, year=year)
    month_verbose = num_to_word(month)
    recipient = Settings.load().reports_email
    attachments = []

    if request.POST.get('action') == 'submit_report':
        job_records = JobRecord.objects.filter(report=report)

        worker_days = {}
        jobs = []
        for record in job_records:
            workers = []
            for shift in record.shifts.all():
                workers.append(f'\t{shift.worker.name}: {shift.days}\n')

                worker_days[shift.worker.name] = (
                    worker_days.get(shift.worker.name, 0)
                    + shift.days
                )

            jobs.append(
                f'{record.date}: {record.job_description}\n'
                f'исполнители:\n{"".join(workers)}\n'
            )

        worker_days_representation = (
            ''.join([c for c in str(worker_days) if c not in "{}'"])
            .replace(',', '\n')
        )

        subject = (
            f'Ежемесячный отчёт по объекту ЖК Platinum за {month_verbose}'
        )
        message = (
            f'Это автоматическое оповещение о завершении работ в '
            f'{decline(month_verbose, "prepositional")} {year}\n'
            f'Ниже приведена краткая сводка по работам за месяц:\n\n'
            f'{worker_days_representation}\n\n'
            f'\n\n{"".join(jobs)}'
        )

    elif request.POST.get('action') == 'approve_report':
        subject = f'Извещение об утверждении отчёта за {month_verbose}'
        message = (
            f'Это автоматическое оповещение об утверждении отчёта '
            f'по выполненным работам за {month_verbose} {year}\n\n'
            f'Отчёт проверен и утверждён. Требуется подготовить документы.'
        )

    elif request.POST.get('action') == 'docs_prepare':
        subject = f'Документы по ЖК Platinum за {month_verbose}'
        message = ''

        date = request.POST.get('custom_date')
        if date:
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            date = date_obj.strftime('%d.%m.%Y')

        email = request.POST.get('email')
        if email and email != 'example@email.com':
            recipient = email

        man_days = int(request.POST.get('man_days'))

        jobs_report = '\n'.join(
            [
                (f'{job.date}: ' if job.date else '')
                + f'{job.job_description}' for job in report.jobs.all()
            ]
        )

        args = [man_days, jobs_report, report.month, report.year, Settings.load().stake]
        if date:
            args.append(date)

        attachments.append(make_act(*args))
        args.remove(jobs_report)
        attachments.append(make_invoice(*args))

    try:
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient],
        )

        if attachments:
            for attachment in attachments:
                email.attach_file(attachment)

        email.send()
        return HttpResponse(
            format_response(f'Письмо успешно отправлено на почту {recipient}')
        )

    except Exception as e:
        return HttpResponse(
            format_response(
                f'Не удалось отправить письмо по следующей причине: {e}', error=True
            )
        )
