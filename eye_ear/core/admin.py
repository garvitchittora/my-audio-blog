from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Blog)
admin.site.register(User)
admin.site.register(Comment)
admin.site.register(Clap)
admin.site.register(BookMark)
admin.site.register(Topic)
admin.site.register(Tag)
admin.site.register(Views)