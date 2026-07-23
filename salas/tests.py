from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .models import ArquivoSala, Sala


class SalaHomePageTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='professor',
            email='professor@example.com',
            password='senha123',
            is_staff=True,
        )
        self.sala = Sala.objects.create(
            nome='Sala de Matemática',
            senha='1234',
            professor=self.user,
            alunos_podem_enviar=True,
        )

    def test_index_lists_existing_salas_and_shows_create_button(self):
        response = self.client.get(reverse('index'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sala de Matemática')
        self.assertContains(response, 'Servidor de Arquivos Uditech')
        self.assertContains(response, 'Criar sala')
        self.assertNotContains(response, 'Nome da sala')

    def test_admin_can_create_sala_via_homepage(self):
        response = self.client.get(reverse('index'), {'create': '1'})
        self.assertContains(response, 'Conta admin')

        response = self.client.post(reverse('index'), {
            'step': 'auth',
            'admin': self.user.pk,
            'password': 'senha123',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Nome da sala')

        response = self.client.post(reverse('index'), {
            'nome': 'Sala de História',
            'senha': '4321',
            'alunos_podem_enviar': 'on',
        })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Sala.objects.filter(nome='Sala de História').exists())
        sala = Sala.objects.get(nome='Sala de História')
        self.assertEqual(sala.professor, self.user)

    def test_sala_detail_requires_password_and_lists_files(self):
        arquivo = ArquivoSala.objects.create(
            sala=self.sala,
            enviado_por=self.user,
            arquivo=SimpleUploadedFile('material.pdf', b'conteudo', content_type='application/pdf'),
            nome_exibicao='material.pdf',
        )

        response = self.client.get(reverse('sala_detail', args=[self.sala.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Senha da sala')

        response = self.client.post(reverse('sala_detail', args=[self.sala.pk]), {'senha': '1234'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'material.pdf')
        self.assertContains(response, 'Arraste e solte arquivos aqui')

        response = self.client.post(reverse('sala_detail', args=[self.sala.pk]), {'senha': 'senha-errada'})
        self.assertContains(response, 'Senha incorreta')
