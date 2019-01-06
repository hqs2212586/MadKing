from django.contrib import admin

# Register your models here.
from assets import models


admin.site.register(models.Asset)