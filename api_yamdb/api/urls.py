from django.urls import include, path

urlpatterns = [
    path('v1/', include('api.api_v1.urls')),
]
