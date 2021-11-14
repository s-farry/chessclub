from django.contrib.admin import AdminSite
from django.utils.translation import ugettext_lazy

from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin

class MyAdminSite(AdminSite):
    # Text to put at the end of each page's <title>.
    site_title = ugettext_lazy('Wallasey Chess Club')

    # Text to put in each page's <h1> (and above login form).
    site_header = ugettext_lazy('Wallasey Chess Club Administration')

    # Text to put at the top of the admin index page.
    index_title = ugettext_lazy('Admin')

    def has_module_permission(self,request):
        return True

admin_site = MyAdminSite()

admin_site.register(User, UserAdmin)
admin_site.register(Group, GroupAdmin)