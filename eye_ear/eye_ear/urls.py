from django.contrib import admin
from django.urls import path, include

from django.conf import settings 
from django.conf.urls.static import static 
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib.sitemaps.views import sitemap
from .sitemaps import BlogSitemap

sitemaps = {
    'Blog': BlogSitemap
}

urlpatterns = static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + [
    path('admin/', admin.site.urls),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('',include("core.urls")),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/', include('allauth.urls')),
]

urlpatterns += staticfiles_urlpatterns()