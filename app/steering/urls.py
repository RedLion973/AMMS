from django.conf.urls.defaults import patterns, url
from app.steering.views import IterationDetailView, SubjectCreateView, SubjectDetailView, ReplyCreateView, ReportListView, ReportDetailView

urlpatterns = patterns('',
    url(r'^reports/$', ReportListView.as_view(), name="reports-list"),
    url(r'^reports/(?P<report_id>\d+)/$', ReportListView.as_view(), name="report-detail"),
    url(r'^(?P<iteration_slug>[-\w]+)/$', IterationDetailView.as_view(), name="iteration-detail"),
    url(r'^(?P<iteration_slug>[-\w]+)/subjects/add/$', SubjectCreateView.as_view(), name="subject-create"),
    url(r'^(?P<iteration_slug>[-\w]+)/subjects/(?P<subject_id>\d+)/(?P<subject_slug>[-\w]+)/$', SubjectDetailView.as_view(), name="subject-detail"),
    url(r'^(?P<iteration_slug>[-\w]+)/subjects/(?P<subject_id>\d+)/(?P<subject_slug>[-\w]+)/reply/add/$', ReplyCreateView.as_view(), name="reply-create"),
)
