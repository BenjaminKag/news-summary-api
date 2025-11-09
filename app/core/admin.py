from django.contrib import admin
from .models import Source, Topic, Article, Summary

admin.site.register(Source)
admin.site.register(Topic)
admin.site.register(Article)
admin.site.register(Summary)
