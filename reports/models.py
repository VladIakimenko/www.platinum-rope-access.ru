from django.db import models
from django.core.validators import MinValueValidator


class Settings(models.Model):
    stake = models.IntegerField(null=False, blank=False)
    reports_email = models.CharField(max_length=60, null=False, blank=False)

    class Meta:
        verbose_name = "настройки"
        verbose_name_plural = "настройки"

    def save(self, *args, **kwargs):
        """Ensure that there is always just one settings object, its pk=1"""
        self.pk = 1
        super(Settings, self).save(*args, **kwargs)
        Settings.objects.exclude(pk=self.pk).delete()

    @classmethod
    def load(cls):
        """Convenience method. Allows using Settings.load()
        to get the only settings instance"""
        obj = cls.objects.get(pk=1)
        return obj


class Report(models.Model):
    month = models.IntegerField(null=False, blank=False, verbose_name='месяц')
    year = models.IntegerField(null=False, blank=False, verbose_name='год')
    stake = models.IntegerField(
        default=None,
        verbose_name='стоимость за 1 ч/д'
    )

    class Meta:
        verbose_name = "ежемесячный отчёт"
        verbose_name_plural = "отчёты"
        ordering = ['-year', '-month']
        unique_together = [['month', 'year']]

    def __str__(self):
        return f'{self.month}.{self.year}'

    def save(self, *args, **kwargs):
        """Use default daily stake if not specified otherwise"""
        if self.stake is None:
            self.stake = Settings.load().stake
        super().save(*args, **kwargs)


class Worker(models.Model):
    name = models.CharField(
        max_length=60,
        null=False,
        blank=False,
        unique=True
    )

    class Meta:
        verbose_name = 'исполнитель'
        verbose_name_plural = 'исполнители'

    def __str__(self):
        return f'{self.name}'


class WorkerJobRecord(models.Model):
    worker = models.ForeignKey(
        'Worker', on_delete=models.PROTECT, null=True,
        blank=True, related_name='shifts'
    )
    job_record = models.ForeignKey(
        'JobRecord', on_delete=models.CASCADE,
        related_name='shifts'
    )
    days = models.IntegerField(null=False, validators=[MinValueValidator(1)])

    def __str__(self):
        return (
            f'worker {self.worker} at job:{self.job_record}'
            f'during {self.days} days'
        )


class JobRecord(models.Model):
    report = models.ForeignKey(
        Report, on_delete=models.CASCADE,
        verbose_name='месяц', related_name='jobs'
    )
    job_description = models.CharField(
        max_length=300, verbose_name='описание работ'
    )
    workers = models.ManyToManyField(
        to='Worker', related_name='job',
        through='WorkerJobRecord', verbose_name='исполнители'
    )
    date = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = 'работы'
        verbose_name_plural = 'перечень работ'
        ordering = ['report__year', 'report__month', 'date']

    def __str__(self):
        return f'{self.date} {self.job_description}'
