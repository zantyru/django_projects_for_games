from django.contrib.admin import AdminSite, ModelAdmin, TabularInline
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


class GameTriangleRacerAdminSite(AdminSite):
    site_header = 'Triangle Racer'


class ConfigOfInitialPlayerResourceAdmin(ModelAdmin):
    list_display = ('resource', 'initial_count', )


class ConfigOfInitialPlayerCostumeAdmin(ModelAdmin):
    list_display = ('costume', )


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


class TimerAdmin(ModelAdmin):
    list_display = ('name', 'duration', )


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
                    'name', 'price',
                ),
            },
        ),
    )

    inlines = [ShopSetComponentInline]


admin_site = GameTriangleRacerAdminSite(name='game_triangle_racer_admin')
admin_site.register(Config)
admin_site.register(ConfigOfInitialPlayerResource, ConfigOfInitialPlayerResourceAdmin)
admin_site.register(ConfigOfInitialPlayerCostume, ConfigOfInitialPlayerCostumeAdmin)
admin_site.register(Player, PlayerAdmin)
admin_site.register(Resource)
admin_site.register(Costume)
admin_site.register(Timer, TimerAdmin)
# admin_site.register(PlayerResource)
# admin_site.register(PlayerCostume)
# admin_site.register(PlayerTimer)
admin_site.register(ShopSet, ShopSetAdmin)
# admin_site.register(ShopSetComponent)
