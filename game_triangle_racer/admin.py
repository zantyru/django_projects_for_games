from django.contrib import admin
from django.contrib.admin import ModelAdmin, TabularInline
from game_triangle_racer.models import (
    Config,
    ConfigOfInitialPlayerResource,
    ConfigOfInitialPlayerCostume,
    Player,
    Resource,
    Costume,
    Timer,
    PlayerResource,
    PlayerCostume,
    PlayerTimer,
    ShopSet,
    ShopSetComponent,
)


# ConfigOfInitialPlayerResourceAdmin

class ConfigOfInitialPlayerResourceAdmin(ModelAdmin):
    list_display = ('resource', 'initial_count', )


# ConfigOfInitialPlayerCostumeAdmin

class ConfigOfInitialPlayerCostumeAdmin(ModelAdmin):
    list_display = ('costume', )


# PlayerAdmin

class PlayerResourceInline(TabularInline):
    model = PlayerResource
    fields = ('resource', 'count', )
    extra = 0


class PlayerCostumeInline(TabularInline):
    model = PlayerCostume
    fields = ('costume', )
    extra = 0


class PlayerTimerInline(TabularInline):
    model = PlayerTimer
    fields = ('timer', 'start_datetime', 'remaining', )
    extra = 0


class PlayerAdmin(ModelAdmin):
    list_display = ('game_id', 'platform', 'platform_id', )
    list_filter = ('platform', )

    fieldsets = (
        (
            'Идентификаторы игрока',
            {
                'fields': (
                    ('platform', 'platform_id', ),
                ),
            },
        ),
        (
            'Регистрация и время последнего входа',
            {
                'fields': (
                    ('regin_stamp', 'login_stamp', 'start_stamp', ),
                ),
            },
        ),
        (
            'Параметры сессии',
            {
                'fields': (
                    ('token', 'token_expiration', ), 'session_quasisecret',
                ),
            },
        ),
        (
            'Уровень',
            {
                'fields': (
                    'level',
                ),
            },
        ),
    )
    inlines = [PlayerResourceInline, PlayerCostumeInline, PlayerTimerInline]


# TimerAdmin

class TimerAdmin(ModelAdmin):
    list_display = ('name', 'duration', )


# ShopSetAdmin

class ShopSetComponentInline(TabularInline):
    model = ShopSetComponent
    extra = 0


class ShopSetAdmin(ModelAdmin):
    list_display = ('name', 'price', )
    list_filter = ('price', )

    fieldsets = (
        (
            'Общие настройки',
            {
                'fields': (
                    'name',
                ),
            },
        ),
        (
            'Цена',
            {
                'fields': (
                    'price',
                ),
            }
        ),
    )

    inlines = [ShopSetComponentInline]


admin.site.register(Config)
admin.site.register(ConfigOfInitialPlayerResource, ConfigOfInitialPlayerResourceAdmin)
admin.site.register(ConfigOfInitialPlayerCostume, ConfigOfInitialPlayerCostumeAdmin)
admin.site.register(Player, PlayerAdmin)
admin.site.register(Resource)
admin.site.register(Costume)
admin.site.register(Timer, TimerAdmin)
# admin.site.register(PlayerResource)
# admin.site.register(PlayerCostume)
# admin.site.register(PlayerTimer)
admin.site.register(ShopSet, ShopSetAdmin)
# admin.site.register(ShopSetComponent)
