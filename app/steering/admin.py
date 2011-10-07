from django.contrib import admin
from app.steering.models import Tag, State, Iteration, Subject, Reply, Report
from app.steering.forms import IterationForm, StateForm

class IterationAdmin(admin.ModelAdmin):
    form = IterationForm
    list_display = ('project', 'name', 'current')
    list_display_links = ('name',)
    list_filter = ['project', 'current',]

class StateAdmin(admin.ModelAdmin):
    form = StateForm
    list_display = ('name', 'type', 'rank')
    list_display_links = ('name',)
    
class ReportAdmin(admin.ModelAdmin):
    list_display = ('project', 'date')
    list_display_links = ('date',)
    list_filter = ['project',]

admin.site.register(Tag)
admin.site.register(Iteration, IterationAdmin)
admin.site.register(Subject)
admin.site.register(Reply)
admin.site.register(State, StateAdmin)
admin.site.register(Report, ReportAdmin)
