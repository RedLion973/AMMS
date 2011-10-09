import ast
from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.exceptions import ImproperlyConfigured
from app.frontend.views import PermissionRequiredMixin
from app.core.models import Project, ProjectActor
from app.steering.models import Iteration, Subject, Tag, State, Reply, Report
from app.steering.forms import SubjectForm, ReplyForm

class ReportListView(PermissionRequiredMixin, ListView):
    permission_required = 'core.view_project'
    context_object_name = "reports_list"
    template_name = "steering/reports_list.html"
    
    def get_queryset(self, **kwargs):
        return Report.objects.filter(project=Project.objects.get(slug=self.kwargs['project_slug'])).order_by('-date')
    
    def get_object(self, **kwargs):
        object = Project.objects.get(slug=self.kwargs['project_slug'])
        return object

    def get_context_data(self, **kwargs):
        context = super(ReportListView, self).get_context_data(**kwargs)
        context.update({
            'project': self.get_object(),
            'last_report': Report.objects.filter(project=Project.objects.get(slug=self.kwargs['project_slug'])).order_by('-date')[0]
        })
        return context

class ReportDetailView(PermissionRequiredMixin, DetailView):
    permission_required = 'steering.view_report'
    context_object_name = "report"
    model = Report
    template_name = "steering/report_detail.html"
    
    def get_object(self, **kwargs):
        object = Report.objects.get(id=self.kwargs['report_id'])
        return object

    def get_context_data(self, **kwargs):
        context = super(ReportDetailView, self).get_context_data(**kwargs)
        elements_list = []
        elements_list.append(self.object.current_iteration)
        new_subjects = ast.literal_eval(self.object.new_subjects)
        open_subjects = ast.literal_eval(self.object.open_subjects)
        closed_solved_subjects = ast.literal_eval(self.object.closed_solved_subjects)
        closed_unsolved_subjects = ast.literal_eval(self.object.closed_unsolved_subjects)
        chart_table = []
        item_open = {}
        item_open.update({
            'label': 'Open',
            'value': str(float(open_subjects['total']) / float(self.object.current_iteration.total_subjects) * 100) + '%'
        })
        chart_table.append(item_open)
        item_closed_u = {}
        item_closed_u.update({
            'label': 'Unsolved',
            'value': str(float(closed_unsolved_subjects['total']) / float(self.object.current_iteration.total_subjects) * 100) + '%'
        })
        chart_table.append(item_closed_u)
        item_closed_s = {}
        item_closed_s.update({
            'label': 'Solved',
            'value': str(float(closed_solved_subjects['total']) / float(self.object.current_iteration.total_subjects) * 100) + '%'
        })
        chart_table.append(item_closed_s)
        print chart_table
        context.update({
            'project': Project.objects.get(slug=self.kwargs['project_slug']),
            'elements_list': elements_list,
            'new_subjects': new_subjects,
            'open_subjects': open_subjects,
            'closed_solved_subjects': closed_solved_subjects,
            'closed_unsolved_subjects': closed_unsolved_subjects,
            'chart_table': chart_table
        })
        return context

class IterationDetailView(PermissionRequiredMixin, DetailView):
    permission_required = 'steering.view_iteration'
    model = Iteration
    context_object_name = "iteration"
    template_name = "steering/iteration_detail.html"
    
    def get_object(self, **kwargs):
        object = Iteration.objects.get(slug=self.kwargs['iteration_slug'])
        return object

    def get_context_data(self, **kwargs):
        context = super(IterationDetailView, self).get_context_data(**kwargs)
        elements_list = []
        elements_list.append(self.object)
        context.update({
            'subjects': self.object.subjects.all().order_by('state__rank'),
            'project': self.object.project,
            'elements_list': elements_list
        })
        return context

class SubjectCreateView(PermissionRequiredMixin, CreateView):
    permission_required = 'steering.view_iteration'
    model = Subject
    form_class = SubjectForm
    template_name = "steering/subject_create.html"
    tags = []

    def get_object(self, **kwargs):
        object = Iteration.objects.get(slug=self.kwargs['iteration_slug'])
        return object

    def post(self, request, *args, **kwargs):
        tags_str = self.request.POST['tags']
        tags_list = tags_str.split(',')
        for t in tags_list:
            self.tags.append(t)
        subject = Subject(name=request.POST['name'], content=request.POST['content'])
        project = Project.objects.get(slug=self.kwargs['project_slug'])
        subject.author=ProjectActor.objects.get(user=self.request.user, project=project)
        subject.iteration=Iteration.objects.get(slug=self.kwargs['iteration_slug'])
        subject.state=State.objects.get(name='Open')
        subject.save()
        for tag in self.tags:
            if tag != '' and tag != ' ' and tag != '  ':
                t, created = Tag.objects.get_or_create(name=tag, defaults={'content_object': subject})
        if "thirdparty.notification" in settings.INSTALLED_APPS:
            from thirdparty.notification import models as notification
            to_users = []
            for actor in project.actors.all():
                if actor != subject.author:
                    to_users.append(actor.user)
            notification.queue(to_users, "new_subject_posted", {'subject': subject})
        return HttpResponseRedirect(subject.get_absolute_url())
    
    def get_context_data(self, **kwargs):
        context = super(SubjectCreateView, self).get_context_data(**kwargs)
        context.update({
            'iteration': Iteration.objects.get(slug=self.kwargs['iteration_slug']),
            'project': Project.objects.get(slug=self.kwargs['project_slug']),
            'tags_already_used': Tag.objects.filter(subject__iteration__project=Project.objects.get(slug=self.kwargs['project_slug'])).order_by('?')[:10]
        })
        return context

class SubjectDetailView(PermissionRequiredMixin, DetailView):
    permission_required = 'steering.view_subject'
    model = Subject
    context_object_name = "subject"
    template_name = "steering/subject_detail.html"

    def get_object(self, **kwargs):
        object = Subject.objects.get(id=self.kwargs['subject_id'])
        return object

    def get_context_data(self, **kwargs):
        context = super(SubjectDetailView, self).get_context_data(**kwargs)
        context.update({
            'project': self.object.iteration.project,
            'iteration': self.object.iteration,
            'reply_form': ReplyForm(),
            'replies': self.object.replies
        })
        return context

class ReplyCreateView(PermissionRequiredMixin, CreateView):
    permission_required = 'steering.view_subject'
    model = Reply
    form_class = ReplyForm
    template_name = "steering/subject_detail.html"

    def get_object(self, **kwargs):
        object = Subject.objects.get(id=self.kwargs['subject_id'])
        return object

    def post(self, request, *args, **kwargs):
        reply = Reply(title=request.POST['title'], content=request.POST['content'])
        project = Project.objects.get(slug=self.kwargs['project_slug'])
        reply.author=ProjectActor.objects.get(user=self.request.user, project=project)
        reply.subject=Subject.objects.get(id=self.kwargs['subject_id'])
        reply.save()
        if "thirdparty.notification" in settings.INSTALLED_APPS:
            from thirdparty.notification import models as notification
            to_users = []
            for actor in project.actors.all():
                if actor != reply.author:
                    to_users.append(actor.user)
            notification.queue(to_users, "new_reply_posted", {'reply': reply})
        return HttpResponseRedirect(reply.subject.get_absolute_url())

