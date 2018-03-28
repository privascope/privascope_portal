from django.contrib import admin

from fsm_admin.mixins import FSMTransitionMixin
from django_fsm_log.admin import StateLogInline


from .models import Job, Comment


class CommentsInline(admin.StackedInline):
    model = Comment
    extra = 0
    readonly_fields = ['timestamp',]


@admin.register(Job)
class JobAdmin(FSMTransitionMixin, admin.ModelAdmin):
    fsm_field = ['status',]
    inlines = [StateLogInline, CommentsInline,]
    readonly_fields = ['status','submitted_at',]
    exclude = ['file','output',]
