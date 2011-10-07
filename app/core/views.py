from django.views.generic import DetailView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, HttpResponseForbidden
from app.frontend.views import PermissionRequiredMixin
from app.core.models import Project, ProjectActor
from app.steering.models import Iteration
from thirdparty.guardian.decorators import permission_required_or_403

class ProjectDetailView(PermissionRequiredMixin, DetailView):
    permission_required = 'core.view_project'
    model = Project
    context_object_name = "project"
    template_name = "core/project_detail.html"
    
    def get_object(self, **kwargs):
        object = Project.objects.get(slug=self.kwargs['project_slug'])
        return object

    def get_context_data(self, **kwargs):
        context = super(ProjectDetailView, self).get_context_data(**kwargs)
        elements_list = []
        for iteration in self.object.iterations.all():
            elements_list.append(iteration)
        context.update({
            'iterations': self.object.iterations.all().order_by('rank'),
            'actors': self.object.actors.all(),
            'elements_list': elements_list
        })
        return context

class ProjectActorDetailView(PermissionRequiredMixin, DetailView):
    permission_required = 'core.view_projectactor'
    model = ProjectActor
    context_object_name = "actor"
    template_name = "core/projectactor_detail.html"

    def get_object(self, **kwargs):
        object = ProjectActor.objects.get(id=self.kwargs['projectactor_id'])
        return object

    def get_context_data(self, **kwargs):
        context = super(ProjectActorDetailView, self).get_context_data(**kwargs)
        context.update({
            'project': Project.objects.get(slug=self.kwargs['project_slug'])
        })
        return context
