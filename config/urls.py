"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from accounts import views as accounts_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),            # signup
    path('accounts/', include('django.contrib.auth.urls')),  # login, logout, password
    # Public user profiles. The "@" prefix keeps usernames out of the Blog
    # slug namespace (slug routes can't match "@", so order is not critical).
    path('@<str:username>/', accounts_views.profile, name='profile'),
    # Blog slugs live at the top level (site.com/{blog-slug}/...), so this
    # include must come last. Slugs colliding with reserved paths like
    # "admin" are shadowed — to be handled with a reserved-slug list later.
    path('', include('blog.urls')),
]

# Serve user-uploaded media from the local filesystem during development.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
