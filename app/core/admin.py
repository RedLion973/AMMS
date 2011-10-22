from django.contrib import admin
from app.core.models import Company, UserProfile, Project, BusinessRole, ProjectRole, ProjectActor, Document, Version

class ProjectActorAdmin(admin.ModelAdmin):
    list_display = ('project', 'full_name', 'full_project_roles', 'full_business_roles')
    list_display_links = ('full_name',)
    list_filter = ['project']

class VersionInline(admin.StackedInline):
    model = Version
    extra = 1
    
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('name', 'project')
    list_display_links = ('name',)
    list_filter = ['project']
    inlines = [VersionInline,]

admin.site.register(Company)
admin.site.register(UserProfile)
admin.site.register(Project)
admin.site.register(ProjectRole)
admin.site.register(BusinessRole)
admin.site.register(ProjectActor, ProjectActorAdmin)
admin.site.register(Document, DocumentAdmin)