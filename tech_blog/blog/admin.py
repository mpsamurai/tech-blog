from django.contrib import admin
from django.conf.urls import url
from django.http import HttpResponse
from django.template.response import TemplateResponse

# Register your models here.

from .models import Top, Article, ArticleTag


@admin.register(Top)
class TopAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'update_at', 'is_used')
    ordering = ['update_at']


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('created_date',
                    'updated_date',
                    'title',
                    'article',
                    'get_employee',
                    'get_member',
                    'get_tags',
                    'is_topic')

    def get_employee(self, obj):
        return ",".join([e.name for e in obj.employee.all()])

    def get_member(self, obj):
        return ",".join([m.name for m in obj.member.all()])

    def get_tags(self, obj):
        return ",".join([m.name for m in obj.tags.all()])


@admin.register(ArticleTag)
class ArticleTagAdmin(admin.ModelAdmin):
    list_display = ('name',)
