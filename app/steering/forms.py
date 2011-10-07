from django import forms
from django.conf import settings
from app.steering.models import Iteration, Subject, Reply, State
from thirdparty.tinymce.widgets import TinyMCE

class IterationForm(forms.ModelForm):
    description = forms.CharField(widget=TinyMCE(attrs={'cols': 100, 'rows': 8}))
    state = forms.ModelChoiceField(queryset=State.objects.filter(type='iteration'))

    class Meta:
        model = Iteration

class SubjectForm(forms.ModelForm):
    content = forms.CharField(widget=TinyMCE(attrs={'cols': 100, 'rows': 10}))

    class Meta:
        model = Subject
        fields = ('name', 'content')

class ReplyForm(forms.ModelForm):
    title = forms.CharField(widget=forms.TextInput(attrs={'size': '50', 'class': 'required'}))
    content = forms.CharField(widget=TinyMCE(attrs={'cols': 100, 'rows': 8, 'class': 'required'}))

    class Meta:
        model = Reply
        fields = ('title', 'content')

class StateForm(forms.ModelForm):
    STATE_CHOICES = []
    STATE_TYPE = []
    for choice in settings.STEERING_STATES:
        STATE_CHOICES.append((choice[0], choice[0]))
        STATE_TYPE.append((choice[0], choice[1]))
        
    name = forms.ChoiceField(choices=STATE_CHOICES)
    
    def save(self, commit=True, force_insert=False, force_update=False):
        state = super(StateForm, self).save(commit=False)
        for type in self.STATE_TYPE:
            print type
            if type[0] == state.name: 
                state.type = type[1]
                break
        if commit:
            state.save()
        return state 
            
    class Meta:
        model = State
        fields = ('name', 'rank', 'icon')
        