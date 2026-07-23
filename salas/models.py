from django.db import models
from django.contrib.auth.models import User

class Sala(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    senha = models.CharField(
        max_length=50,
        blank=True,
        default='',
        verbose_name="Senha de acesso (alunos)",
        help_text="Deixe vazio para sala sem senha para alunos.",
    )
    professor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='salas')
    
    alunos_podem_enviar = models.BooleanField(default=False, verbose_name="Alunos podem subir arquivos?")
    criada_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome

class ArquivoSala(models.Model):
    sala = models.ForeignKey(Sala, on_delete=models.CASCADE, related_name='arquivos')
    enviado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    arquivo = models.FileField(upload_to='arquivos_salas/')
    nome_exibicao = models.CharField(max_length=255)
    enviado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nome_exibicao} ({self.sala.nome})"


from django.db.models.signals import post_delete
from django.dispatch import receiver


@receiver(post_delete, sender=ArquivoSala)
def delete_arquivo_file(sender, instance, **kwargs):
    if instance.arquivo:
        instance.arquivo.delete(save=False)