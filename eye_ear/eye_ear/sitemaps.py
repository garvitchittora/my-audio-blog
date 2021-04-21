from django.contrib.sitemaps import Sitemap
from django.core.paginator import Paginator
from django.urls import reverse
from core.models import Blog

class BlogSitemap(Sitemap):

    def items(self):
        objects = Blog.objects.all()
        # paginator = Paginator(objects, 50000)
        # return paginator.page_range
        return objects
    
    def lastmod(self, obj):
        return obj.updated_at