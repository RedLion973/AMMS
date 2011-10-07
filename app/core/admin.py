from django.contrib import admin
from app.core.models import Company, UserProfile, Project, BusinessRole, ProjectRole, ProjectActor

class ProjectActorAdmin(admin.ModelAdmin):
    list_display = ('project', 'full_name', 'full_project_roles', 'full_business_roles')
    list_display_links = ('full_name',)
    list_filter = ['project']

admin.site.register(Company)
admin.site.register(UserProfile)
admin.site.register(Project)
admin.site.register(ProjectRole)
admin.site.register(BusinessRole)
admin.site.register(ProjectActor, ProjectActorAdmin)