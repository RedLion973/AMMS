from django.conf.urls.defaults import patterns, include, url
from app.core.views import ProjectDetailView, ProjectActorDetailView, DocumentDetailView

urlpatterns = patterns('',
    url(r'^(?P<project_slug>[-\w]+)/$', ProjectDetailView.as_view(), name="project-detail"),
    url(r'^(?P<project_slug>[-\w]+)/projectactors/(?P<projectactor_id>\d+)/$', ProjectActorDetailView.as_view(), name="projectactor-detail"),
    url(r'^(?P<project_slug>[-\w]+)/documents/(?P<document_id>\d+)/$', DocumentDetailView.as_view(), name="document-detail"),
    url(r'^(?P<project_slug>[-\w]+)/iterations/', include('app.steering.urls')),
)
