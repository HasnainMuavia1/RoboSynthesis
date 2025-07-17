from django.urls import path
from . import views

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
]
