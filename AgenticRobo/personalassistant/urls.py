from django.urls import path
from . import views
from . import drive_views

app_name = 'personalassistant'

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('agento-assistant/', views.agento_assistant, name='agento_assistant'),
    path('ai-tutor/', views.ai_tutor, name='ai_tutor'),
    path('mcp-config/', views.mcp_config, name='mcp_config'),
    
    # API endpoints - match the frontend URL expectations
    path('api/tavily-search/', views.tavily_search, name='tavily_search'),
    path('api/message/', views.message_api, name='message_api'),
    path('api/upload/', views.upload_file, name='upload_file'),
    
    # Subject tutor endpoints
    path('subject-tutor/<str:subject>/', views.subject_tutor, name='subject_tutor'),
    path('save_subject_context/', views.save_subject_context, name='save_subject_context'),
    path('subject_message/', views.subject_message, name='subject_message'),
    
    # MCP Config endpoints
    path('upload_mcp_config/', views.upload_mcp_config, name='upload_mcp_config'),
    path('save_github_token/', views.save_github_token, name='save_github_token'),
    path('disconnect_mcp/', views.disconnect_mcp, name='disconnect_mcp'),
    
    # Google Drive API endpoints
    path('api/drive/files/', drive_views.list_drive_files, name='list_drive_files'),
    path('api/drive/files/<str:file_type>/', drive_views.list_drive_files_by_type, name='list_drive_files_by_type'),
    path('api/drive/file/<str:file_id>/', drive_views.read_drive_file, name='read_drive_file'),
    path('api/drive/create/', drive_views.create_drive_file, name='create_drive_file'),
    path('api/drive/create-excel/', drive_views.create_drive_excel, name='create_drive_excel'),
    path('check_mcp_status/', views.check_mcp_status, name='check_mcp_status'),
    
    # IBM Watson speech services
    path('api/watson/speech-to-text/', views.watson_speech_to_text, name='watson_speech_to_text'),
    path('api/watson/text-to-speech/', views.watson_text_to_speech, name='watson_text_to_speech'),
]
