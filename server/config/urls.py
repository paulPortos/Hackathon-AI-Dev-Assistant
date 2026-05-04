from django.contrib import admin
from django.urls import include, path

from users.urls import auth_urlpatterns


urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include((auth_urlpatterns, 'auth'), namespace='auth')),
    path('', include('user_descriptions.urls')),
    path('', include('users.urls')),
]
