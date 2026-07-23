from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Sala


class ProfessorCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']
        labels = {
            'username': 'Usuário do professor',
            'password1': 'Senha',
            'password2': 'Confirme a senha',
        }


class SalaForm(forms.ModelForm):
    class Meta:
        model = Sala
        fields = ['nome', 'senha', 'alunos_podem_enviar']
        widgets = {
            'senha': forms.PasswordInput(render_value=True),
        }
        labels = {
            'nome': 'Nome da sala',
            'senha': 'Senha dos alunos (opcional)',
            'alunos_podem_enviar': 'Permitir que alunos enviem arquivos',
        }


class SalaCreateForm(SalaForm):
    class Meta(SalaForm.Meta):
        fields = ['nome', 'senha', 'professor', 'alunos_podem_enviar']
        labels = {
            **SalaForm.Meta.labels,
            'professor': 'Professor responsável',
        }
        widgets = {
            **SalaForm.Meta.widgets,
            'senha': forms.PasswordInput(render_value=True),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['professor'].queryset = User.objects.filter(is_staff=False).order_by('username')
        self.fields['professor'].help_text = 'Escolha um professor já cadastrado para vincular à sala.'
