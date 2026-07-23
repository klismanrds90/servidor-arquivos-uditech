from asgiref.sync import async_to_sync
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .consumers import notify_sala_change
from .forms import ProfessorCreationForm, SalaCreateForm, SalaForm
from .models import ArquivoSala, Sala


def can_manage_sala(user, sala):
    return user.is_authenticated and (user.is_staff or user == sala.professor)


def index(request):
    salas = Sala.objects.select_related('professor').order_by('-criada_em')
    user_authenticated = request.user.is_authenticated
    is_staff = user_authenticated and request.user.is_staff
    is_professor = user_authenticated and not request.user.is_staff
    login_type = request.GET.get('login')
    show_create_flow = request.GET.get('create') == '1' or request.session.get('admin_create_id') is not None
    show_login_form = login_type in ['admin', 'professor'] and not user_authenticated and not show_create_flow

    professor_form = ProfessorCreationForm()
    sala_form = SalaForm()
    login_error = None
    create_error = None
    professor_error = None
    professor_success = None
    sala_success = None
    admin_auth_error = None
    admin_accounts = get_user_model().objects.filter(is_staff=True).order_by('username')
    admin_create_id = None

    if request.method == 'POST':
        action = request.POST.get('action')
        step = request.POST.get('step')

        if step == 'auth':
            admin_id = request.POST.get('admin')
            password = request.POST.get('password')
            admin_user = get_user_model().objects.filter(pk=admin_id, is_staff=True).first()
            if admin_user:
                user = authenticate(request, username=admin_user.username, password=password)
                if user and user.is_staff:
                    request.session['admin_create_id'] = user.pk
                    admin_create_id = user.pk
                    show_create_flow = True
                    sala_form = SalaForm()
                else:
                    admin_auth_error = 'Usuário ou senha inválidos para admin.'
                    show_create_flow = True
            else:
                admin_auth_error = 'Conta admin inválida.'
                show_create_flow = True

        elif request.POST.get('nome') and request.session.get('admin_create_id'):
            sala_form = SalaForm(request.POST)
            if sala_form.is_valid():
                admin_user = get_user_model().objects.filter(pk=request.session.get('admin_create_id')).first()
                if admin_user:
                    sala = sala_form.save(commit=False)
                    sala.professor = admin_user
                    sala.save()
                    request.session.pop('admin_create_id', None)
                    return redirect('index')
                create_error = 'Conta admin inválida para criação da sala.'
                show_create_flow = True
            else:
                create_error = 'Corrija os erros do formulário de sala.'
                show_create_flow = True

        elif action == 'login_admin':
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(request, username=username, password=password)
            if user and user.is_staff:
                login(request, user)
                return redirect('index')
            login_error = 'Usuário ou senha inválidos para admin.'
            login_type = 'admin'

        elif action == 'login_professor':
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(request, username=username, password=password)
            if user and not user.is_staff:
                login(request, user)
                return redirect('index')
            login_error = 'Usuário ou senha inválidos para professor.'
            login_type = 'professor'

        elif action == 'create_professor':
            if not is_staff:
                return HttpResponseForbidden()
            professor_form = ProfessorCreationForm(request.POST)
            if professor_form.is_valid():
                professor_form.save()
                professor_success = 'Professor cadastrado com sucesso.'
            else:
                professor_error = 'Corrija os erros do formulário de professor.'

        elif action == 'create_sala':
            if not is_staff:
                return HttpResponseForbidden()
            sala_form = SalaCreateForm(request.POST)
            if sala_form.is_valid():
                sala_form.save()
                sala_success = 'Sala criada com sucesso.'
            else:
                create_error = 'Corrija os erros do formulário de sala.'

    professor_rooms = Sala.objects.filter(professor=request.user).order_by('-criada_em') if is_professor else None

    return render(request, 'salas/index.html', {
        'salas': salas,
        'professor_rooms': professor_rooms,
        'user_authenticated': user_authenticated,
        'is_staff': is_staff,
        'is_professor': is_professor,
        'login_type': login_type,
        'show_login_form': show_login_form,
        'show_create_flow': show_create_flow,
        'show_create_form': bool(admin_create_id),
        'admin_auth_error': admin_auth_error,
        'admin_accounts': admin_accounts,
        'admin_create_id': admin_create_id,
        'professor_form': professor_form,
        'sala_form': sala_form,
        'login_error': login_error,
        'create_error': create_error,
        'professor_error': professor_error,
        'professor_success': professor_success,
        'sala_success': sala_success,
    })


@login_required
def sala_edit(request, pk):
    sala = get_object_or_404(Sala, pk=pk)
    if not can_manage_sala(request.user, sala):
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = SalaForm(request.POST, instance=sala)
        if form.is_valid():
            form.save()
            return redirect('index')
    else:
        form = SalaForm(instance=sala)

    return render(request, 'salas/sala_edit.html', {
        'sala': sala,
        'form': form,
    })


@login_required
def sala_delete(request, pk):
    sala = get_object_or_404(Sala, pk=pk)
    if not can_manage_sala(request.user, sala):
        return HttpResponseForbidden()

    if request.method == 'POST':
        sala.delete()
        return redirect('index')

    return render(request, 'salas/sala_delete.html', {
        'sala': sala,
    })


@login_required
def toggle_upload_permission(request, pk):
    sala = get_object_or_404(Sala, pk=pk)
    if not can_manage_sala(request.user, sala):
        return HttpResponseForbidden()

    sala.alunos_podem_enviar = not sala.alunos_podem_enviar
    sala.save()
    return redirect('sala_detail', pk=sala.pk)


@login_required
def delete_arquivo(request, pk, arquivo_pk):
    sala = get_object_or_404(Sala, pk=pk)
    arquivo = get_object_or_404(ArquivoSala, pk=arquivo_pk, sala=sala)
    if not can_manage_sala(request.user, sala):
        return HttpResponseForbidden()

    arquivo.delete()
    return redirect('sala_detail', pk=sala.pk)


def logout_view(request):
    logout(request)
    return redirect('index')


def sala_detail(request, pk):
    sala = get_object_or_404(Sala, pk=pk)
    senha_error = None
    upload_error = None
    arquivos = sala.arquivos.order_by('-enviado_em')
    can_manage = can_manage_sala(request.user, sala)
    authenticated = request.session.get(f'sala_{sala.pk}_auth', False)

    if request.method == 'POST':
        if 'senha' in request.POST:
            if request.POST.get('senha') == sala.senha:
                authenticated = True
                request.session[f'sala_{sala.pk}_auth'] = True
            else:
                authenticated = False
                request.session[f'sala_{sala.pk}_auth'] = False
                senha_error = 'Senha incorreta.'

        elif request.FILES:
            if not authenticated and not can_manage:
                upload_error = 'Autentique-se primeiro com a senha da sala.'
            elif not sala.alunos_podem_enviar and not can_manage:
                upload_error = 'Esta sala não permite envio de arquivos por alunos.'
            else:
                files = request.FILES.getlist('files')
                if not files:
                    upload_error = 'Nenhum arquivo selecionado.'
                else:
                    for uploaded_file in files:
                        ArquivoSala.objects.create(
                            sala=sala,
                            enviado_por=request.user if request.user.is_authenticated else None,
                            arquivo=uploaded_file,
                            nome_exibicao=uploaded_file.name,
                        )
                    async_to_sync(notify_sala_change)(sala.pk)
                    return redirect('sala_detail', pk=sala.pk)

    if can_manage:
        authenticated = True

    return render(request, 'salas/sala_detail.html', {
        'sala': sala,
        'arquivos': arquivos,
        'authenticated': authenticated,
        'senha_error': senha_error,
        'upload_error': upload_error,
        'can_manage': can_manage,
    })


def sala_arquivos_json(request, pk):
    sala = get_object_or_404(Sala, pk=pk)
    arquivos = sala.arquivos.order_by('-enviado_em').values(
        'pk',
        'nome_exibicao',
        'enviado_em',
        'arquivo',
        'enviado_por__username',
        'arquivo__size',
    )
    data = []
    for arquivo in arquivos:
        data.append({
            'pk': arquivo['pk'],
            'nome_exibicao': arquivo['nome_exibicao'],
            'enviado_por': arquivo['enviado_por__username'] or 'anônimo',
            'enviado_em': arquivo['enviado_em'].strftime('%d/%m/%Y %H:%M'),
            'arquivo_url': request.build_absolute_uri(arquivo['arquivo']),
            'size': arquivo['arquivo__size'],
        })
    return JsonResponse({'arquivos': data})
