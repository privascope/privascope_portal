from django.contrib import admin
from django.urls import path

from . import views

app_name = 'jobs'
urlpatterns = [
    path('', views.home, name='home'),
    # path('login', views.login, name='login'),
    path('logout', views.logout, name='logout'),
    path('jobs', views.index, name='index'),
    path('detail/<int:job_id>', views.details, name='detail'),
    path('history/<int:job_id>', views.history, name='history'),
    path('file/<int:job_id>', views.job_file, name='job_file'),
    path('output/<int:job_id>', views.job_output, name='job_output'),
    path('errors/<int:job_id>', views.job_errors, name='job_errors'),
    path('create', views.CreateView.as_view(), name='create'),
]
