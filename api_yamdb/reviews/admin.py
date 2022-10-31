from django.contrib import admin

from .models import Category, Comment, Genre, GenreTitle, Review, Title, User


class UserAdmin(admin.ModelAdmin):
    list_display = (
        'username', 'email', 'first_name',
        'last_name', 'bio', 'role',
    )
    list_editable = ('role',)
    empty_value_display = '-пусто-'


admin.site.register(User, UserAdmin)
admin.site.register(Category)
admin.site.register(Genre)
admin.site.register(GenreTitle)
admin.site.register(Title)
admin.site.register(Review)
admin.site.register(Comment)
