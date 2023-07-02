from django.contrib import admin
from django.urls import path

from reports.views import login_view, report_view, send_email


urlpatterns = [
    path('', login_view, name='login'),
    path('report/<int:month>-<int:year>/', report_view, name='report'),
    path('email/', send_email, name='send_email'),
]