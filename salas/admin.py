from django.contrib import admin
from .models import Sala, ArquivoSala

@admin.register(Sala)
class SalaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'professor', 'alunos_podem_enviar', 'criada_em')
    search_fields = ('nome', 'professor__username')

@admin.register(ArquivoSala)
class ArquivoSalaAdmin(admin.ModelAdmin):
    list_display = ('nome_exibicao', 'sala', 'enviado_por', 'enviado_em')