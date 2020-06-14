from django.contrib import admin
from .models import news, event
from tinymce.widgets import TinyMCE
from django import forms

# Register your models here.

class NewsAdminForm(forms.ModelForm):
    title = forms.CharField(max_length=50)
    text = forms.CharField(max_length= 10000, widget = TinyMCE(attrs = {'rows' : '30', 'cols' : '100', 'content_style' : "color:#FFFF00", 'body_class': 'review', 'body_id': 'review',}), label='News')
    synopsis = forms.CharField(max_length= 1000, widget = forms.Textarea(attrs = {'rows' : '10', 'cols' : '90'}))

    class Meta:
        fields = ('title', 'synopsis', 'text', 'image')
        model = news

class NewsAdmin(admin.ModelAdmin):
    list_display = ['title', 'status']
    list_filter = [ 'status' ]
    search_fields = [ 'title' ]
    actions = ['make_published']
    
    form = NewsAdminForm
    def make_published(self, request, queryset):
        rows_updated = queryset.update(status='p')
        for obj in queryset:
            obj.status='p'
            obj.published_date = timezone.now()
            obj.save()
        if rows_updated == 1:
            message_bit = "1 news item was"
        else:
            message_bit = "%s news items were" % rows_updated
        self.message_user(request, "%s successfully marked as published." % message_bit)
    make_published.short_description = "Mark selected news items as published"

    def get_form(self, request, obj=None, **kwargs):
        form = super(NewsAdmin, self).get_form(request, obj, **kwargs)
        return form


    def get_readonly_fields(self, request, obj=None):
        return []


admin.site.register(news, NewsAdmin)
admin.site.register(event)