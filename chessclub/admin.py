from django.contrib.admin import AdminSite
from django.utils.translation import ugettext_lazy

from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin

from django.conf.urls import url, include

from content.models import htmlobject

from .views import preview


class MyAdminSite(AdminSite):
    # Text to put at the end of each page's <title>.
    site_title = ugettext_lazy('Wallasey Chess Club')

    # Text to put in each page's <h1> (and above login form).
    site_header = ugettext_lazy('Wallasey Chess Club Administration')

    # Text to put at the top of the admin index page.
    index_title = ugettext_lazy('Admin')

    def has_module_permission(self,request):
        return True

    def get_urls(self):
        urls = super().get_urls()

        my_urls = [
            url(r'^preview/$', self.admin_view(preview))
        ]

        return my_urls + urls

admin_site = MyAdminSite()

admin_site.register(User, UserAdmin)
admin_site.register(Group, GroupAdmin)