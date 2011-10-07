import os
from django.conf import settings
from django.utils.translation import ugettext_noop as _
from django.db.models.signals import post_syncdb
from django.core.files import File
from django.template import defaultfilters
from app.steering import models as steering
from thirdparty.notification import models as notification

def create_notice_types(app, created_models, verbosity, **kwargs):
    notification.create_notice_type("new_subject_posted", _("New Subject Posted"), _("A new subject has been posted"))
    notification.create_notice_type("new_reply_posted", _("New Reply Posted"), _("A new reply has been posted"))
    
post_syncdb.connect(create_notice_types, sender=notification)

def create_states(app, created_models, verbosity=1, **kwargs):
    state_rank = 0    
    for choice in settings.STEERING_STATES:
        f = open(os.path.join(settings.MEDIA_ROOT, 'states_icon/' + defaultfilters.slugify(choice[0]).replace('-','_') + '.png'))
        icon = File(f)
        steering.create_state(choice[0], state_rank, choice[1], icon, verbosity)
        f.close()
        state_rank += 1
    
post_syncdb.connect(create_states, sender=steering)