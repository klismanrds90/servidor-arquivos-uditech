from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('logout/', views.logout_view, name='logout'),
    path('admin/painel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/professores/<int:pk>/editar/', views.professor_edit, name='professor_edit'),
    path('admin/professores/<int:pk>/excluir/', views.professor_delete, name='professor_delete'),
    path('salas/<int:pk>/', views.sala_detail, name='sala_detail'),
    path('salas/<int:pk>/editar/', views.sala_edit, name='sala_edit'),
    path('salas/<int:pk>/excluir/', views.sala_delete, name='sala_delete'),
    path('salas/<int:pk>/toggle-upload/', views.toggle_upload_permission, name='toggle_upload_permission'),
    path('salas/<int:pk>/arquivos/<int:arquivo_pk>/excluir/', views.delete_arquivo, name='delete_arquivo'),
    path('salas/<int:pk>/arquivos/json/', views.sala_arquivos_json, name='sala_arquivos_json'),
]