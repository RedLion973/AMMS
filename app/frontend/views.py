from django.views.generic import ListView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.utils.http import urlquote
from django.conf import settings
from app.core.models import Project
from thirdparty.guardian.shortcuts import get_objects_for_user

class PermissionRequiredMixin(object):
    ### default class view settings
    login_url = settings.LOGIN_URL
    raise_exception = False
    permission_required = None
    redirect_field_name = 'next'

    def dispatch(self, request, *args, **kwargs):
        # call the parent dispatch first to pre-populate few things before we check for permissions
        original_return_value = super(PermissionRequiredMixin, self).dispatch(request, *args, **kwargs)

        # verify class settings
        if self.permission_required == None or len(self.permission_required.split('.')) != 2:
            raise ImproperlyConfigured("'PermissionRequiredMixin' requires 'permission_required' attribute to be set to '<app_label>.<permission codename>' but is set to '%s' instead" % self.permission_required)

        # verify permission on object instance if needed
        has_permission = False
        if hasattr(self, 'object')  and self.object is not None:
            has_permission = request.user.has_perm(self.permission_required, self.object)
        elif hasattr(self, 'get_object') and callable(self.get_object):
            has_permission = request.user.has_perm(self.permission_required, self.get_object())
        else:
            has_permission = request.user.has_perm(self.permission_required)

        # user failed permission
        if not has_permission:
            if self.raise_exception:
                return HttpResponseForbidden()
            else:
                path = urlquote(request.get_full_path())
                tup = self.login_url, self.redirect_field_name, path
                return HttpResponseRedirect("%s?%s=%s" % tup)

        # user passed permission check so just return the result of calling .dispatch()
        return original_return_value

class HomeView(ListView):
    context_object_name = "project_list"
    template_name = "index.html"
    
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(HomeView, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        return get_objects_for_user(self.request.user, 'core.view_project')

