# зовнішній вигляд програми описується в тому (єдиному) екземплярі класу App, 
# у якого викликається run(). 
# import os
# os.environ["KIVY_GL_BACKEND"] = "angle_sdl2"

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition, FadeTransition
from kivy.core.window import Window
from kivy.properties import NumericProperty, BooleanProperty
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior
from kivy.animation import Animation
import random
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.config import Config
# Вимикаємо червоні крапки від "мультитачу" правою кнопкою миші
Config.set('input', 'mouse', 'mouse,disable_multitouch')
Window.size = (390, 844)
# Створимо клас-спадкоємець App. У ньому дописуватиметься функціонал програми.
class MenuScreen(Screen):
    def play_click_sound(self):
        click_sound = App.get_running_app().click_sound
        if click_sound:
            click_sound.play()


    def on_enter(self):
        # Перевіряємо, чи музика вже грає, щоб не запускати її з початку
        App.get_running_app().play_menu_music()

    def go_game(self):
        self.play_click_sound()
        self.manager.transition.direction = 'left'
        self.manager.current = 'game'

    def go_settings(self):
        self.play_click_sound()
        self.manager.transition.direction = 'left'
        self.manager.current = 'settings'

    def exit_app(self):
        self.play_click_sound()
        App.get_running_app().stop()

class FloatingText(Label):
    def __init__(self, start_pos, damage_value="-10", **kwargs):
        super().__init__(**kwargs)
        self.text = damage_value
        # Встановлюємо початкову позицію
        self.center_x = start_pos[0]
        self.center_y = start_pos[1]
        self.animate()

    def animate(self):
        # Текст підійматиметься на 100 пікселів вгору і ставатиме прозорим
        anim = Animation(y=self.y + 100, opacity=0, duration=0.7, t='out_quad')
        # Коли анімація завершиться, видаляємо віджет з екрана, щоб не забивати пам'ять
        anim.bind(on_complete=self.remove_self)
        anim.start(self)

    def remove_self(self, *args):
        if self.parent:
            self.parent.remove_widget(self)

class Target(ButtonBehavior, Image):
    hp = NumericProperty(100) # Здоров'я належить саме цій цілі
    max_hp = NumericProperty(100)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Реєструємо нову подію (як on_press, тільки наша власна)
        self.register_event_type('on_death')
        self.pos_hint = {'center_x': 0.5}
        self.is_appearing = False

    def play_click_target_sound(self):
        app = App.get_running_app()
        click_target_sound = app.click_target_sound
        if click_target_sound and app.sounds_enabled:
            click_target_sound.play()

    def on_press(self):
        if self.is_appearing:
            return  
        Animation.stop_all(self)

        self.play_click_target_sound()
        anim_expand = Animation(size_hint=(0.8, 0.46), duration=0.1, t='out_quad')
        anim_reset = Animation(size_hint=(0.7, 0.4), duration=0.15, t='in_quad')
        full_anim = anim_expand + anim_reset
        full_anim.start(self)
        
        if self.hp > 0:
            # Отримуємо поточне значення урону з налаштувань програми
            app = App.get_running_app()
            damage = app.click_damage
            self.hp -= damage

            offset_x = random.randint(-40, 40)
            offset_y = random.randint(0, 30)
            spawn_pos = (self.center_x + offset_x, self.center_y + offset_y)
            
            # Передаємо динамічне значення у спливаючий текст
            damage_text = FloatingText(start_pos=spawn_pos, damage_value=f"-{damage}")
            self.parent.add_widget(damage_text)
            
            if self.hp <= 0:
                self.hp = 0
                self.dispatch('on_death')


    def appear(self):

        Animation.stop_all(self)
    
        self.opacity = 1  
        self.size_hint = (0.7, 0.4)
        self.is_appearing = True  # Встановлюємо прапорець, що ціль з'являється
        if self.animation == "fly_up":
            self.pos_hint = {"center_x": 0.5, "center_y": -0.5}
            target_pos = {"center_x": 0.5, "center_y": 0.5}
            easing = "out_quad"
        elif self.animation == "enter_right":
            self.pos_hint = {"center_x": 1.5, "center_y": 0.5}
            target_pos = {"center_x": 0.5, "center_y": 0.5}
            easing = "out_bounce"
        elif self.animation == "drop_down":
            self.pos_hint = {"center_x": 0.5, "center_y": 1.5}
            target_pos = {"center_x": 0.5, "center_y": 0.5}
            easing = "out_bounce"
        else:
            self.pos_hint = {"center_x": 0.5, "center_y": 0.5}
            target_pos = {"center_x": 0.5, "center_y": 0.5}
            easing = "linear"
        anim =  Animation(pos_hint=target_pos, duration=0.6, t=easing)
        anim.bind(on_complete=self.on_appear_complete)
        anim.start(self)

    def on_appear_complete(self, *args):
        self.is_appearing = False

    def on_death(self):
        # Kivy вимагає, щоб для події існував порожній метод
        pass

class GameScreen(Screen):

    current_level = NumericProperty(0)
    time_left = NumericProperty(10)
    max_time = NumericProperty(10)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.timer_event = None  # Змінна для зберігання події таймера

    def play_click_sound(self):
        click_sound = App.get_running_app().click_sound
        if click_sound:
            click_sound.play()

    def on_enter(self):
        App.get_running_app().play_game_music()
        self.load_level()

    def load_level(self):
        if self.timer_event:
            self.timer_event.cancel()
            
        # Ховаємо ціль, поки йде анімація напису, і блокуємо передчасні кліки
        self.ids.monster.opacity = 0
        self.ids.monster.is_appearing = True
        
        if self.current_level < len(ClickerApp.levels):
            level_data = ClickerApp.levels[self.current_level]
            self.ids.monster.max_hp = level_data["hp"]
            self.ids.monster.hp = level_data["hp"]
            self.ids.monster.source = level_data["image"]
            self.ids.monster.animation = level_data["animation"]

            # Налаштовуємо таймер, але ще не запускаємо його
            self.max_time = level_data.get("time", 10)
            self.time_left = self.max_time
            
            # --- Анімація напису рівня ---
            popup = self.ids.level_popup
            popup.text = f"Level {self.current_level + 1}"
            
            # Створюємо ланцюжок анімацій: 
            # 1. Залишається видимим 0.5 сек 
            # 2. Плавно зникає 0.5 сек
            anim = Animation(opacity=1, duration=0.5) + Animation(opacity=0, duration=0.5)
            # Після завершення анімації запускаємо геймплей
            anim.bind(on_complete=self.start_level_gameplay)
            anim.start(popup)
        else:
            print("Гру завершено! Всі рівні пройдені.")
            self.go_menu()

    def start_level_gameplay(self, *args):
        # Коли напис зникає, з'являється монстр і запускається таймер
        self.ids.monster.appear()
        self.timer_event = Clock.schedule_interval(self.update_timer, 0.05)

    def level_complete(self):
        if self.timer_event:
            self.timer_event.cancel()
        print(f"Рівень {self.current_level + 1} пройдено!")
        self.current_level += 1
        self.load_level()

    def go_menu(self):
        self.play_click_sound()
        if self.timer_event:
            self.timer_event.cancel()
        self.manager.transition.direction = 'right'
        self.manager.current = 'menu'
        self.current_level = 0  

    def update_timer(self, dt):
        self.time_left -= dt
        if self.time_left <= 0:
            self.time_left = 0
            self.timer_event.cancel()
            self.level_failed()

    def level_failed(self):
        # Логіка програшу. Зараз рівень просто перезапускається
        print("Час вийшов!")
        self.load_level()        
 
class SettingsScreen(Screen):
    def play_click_sound(self):
        click_sound = App.get_running_app().click_sound
        if click_sound:
            click_sound.play()

    def on_enter(self):
        # Перевіряємо, чи музика вже грає, щоб не запускати її з початку
        App.get_running_app().play_menu_music()

    def go_menu(self):
        self.play_click_sound()
        self.manager.transition.direction = 'right'
        self.manager.current = 'menu'    

    def reset_progress(self):
        self.play_click_sound()
        # Отримуємо доступ до ігрового екрана через ScreenManager
        game_screen = self.manager.get_screen('game')
        game_screen.current_level = 0
        game_screen.load_level() # Перезавантажуємо рівень
        print("Прогрес скинуто!")      

class ClickerApp(App):
    sounds_enabled = BooleanProperty(True)
    click_damage = NumericProperty(5)
    menu_music = None
    game_music = None
    click_sound = None
    click_target_sound = None

    levels = [
        {"hp": 50, "image": "assets/images/balloon.png",  "animation": "fly_up"},
        {"hp": 150, "image": "assets/images/monster.png", "animation": "enter_right"},
        {"hp": 300, "image": "assets/images/treasure.png", "animation": "drop_down"}
    ]

    def build(self):
        sm = ScreenManager(transition=SlideTransition())
        sm.add_widget(MenuScreen(name='menu'))
        sm.add_widget(GameScreen(name='game'))
        sm.add_widget(SettingsScreen(name='settings'))
        self.menu_music = SoundLoader.load('assets/audio/Marimba-Dash.mp3') 
        self.game_music = SoundLoader.load('assets/audio/game.mp3')  # Завантажуємо музику для гри
        self.click_sound = SoundLoader.load('assets/audio/btn.mp3')
        self.click_target_sound = SoundLoader.load('assets/audio/squish.mp3')
        if self.menu_music:
            self.menu_music.loop = True
            self.menu_music.volume = 0.3
            
        if self.game_music:
            self.game_music.loop = True
            self.game_music.volume = 0.1
        self.play_menu_music()  # Вмикаємо музику меню при запуску програми
        return sm
    
    def set_difficulty(self, index):
        # Змінюємо урон залежно від індексу слайда в каруселі
        if index == 0:
            self.click_damage = 15  # Легко
        elif index == 1:
            self.click_damage = 10   # Нормально
        elif index == 2:
            self.click_damage = 5   # Складно

    # Метод для увімкнення музики меню
    def play_menu_music(self):
        if self.game_music and self.game_music.state == 'play':
            self.game_music.stop()
        # Перевіряємо, чи музика вже не грає, щоб не запускати її з початку
        if self.menu_music and self.menu_music.state == 'stop':
            self.menu_music.play()

    # Метод для увімкнення музики гри
    def play_game_music(self):
        if self.menu_music and self.menu_music.state == 'play':
            self.menu_music.stop()
        if self.game_music and self.game_music.state == 'stop':
            self.game_music.play()

    def set_music_volume(self, volume):
        # Змінюємо гучність для обох треків, якщо вони існують
        if self.menu_music:
            self.menu_music.volume = volume
        if self.game_music:
            self.game_music.volume = volume

    def toggle_sounds(self, is_active):
        self.sounds_enabled = is_active

app = ClickerApp()
app.run()