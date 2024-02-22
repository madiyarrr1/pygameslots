from player import Player
from reel import *
from settings import *
from ui import UI
from wins import *
import pygame

symbols_values = {
    'crown': 30,
    'chip': 15,
    'seven': 10,
    'cherry': 7,
    'dices': 4
}
class Machine:
    def __init__(self):
        self.display_surface = pygame.display.get_surface()
        self.machine_balance = 10000.00
        self.reel_index = 0
        self.reel_list = {}
        self.can_toggle = True
        self.spinning = False
        self.can_animate = False
        self.win_animation_ongoing = False

        self.prev_result = {0: None, 1: None, 2: None}
        self.spin_result = {0: None, 1: None, 2: None}

        self.spawn_reels()
        self.currPlayer = Player()
        self.ui = UI(self.currPlayer)

    def cooldowns(self):
        for reel in self.reel_list:
            if self.reel_list[reel].reel_is_spinning:
                self.can_toggle = False
                self.spinning = True

        if not self.can_toggle and [self.reel_list[reel].reel_is_spinning for reel in self.reel_list].count(False) == 3:
            self.can_toggle = True
            self.spin_result = self.get_result()

            if self.check_wins(self.spin_result):
                self.win_data = self.check_wins(self.spin_result)
                self.pay_player(self.win_data, self.currPlayer)
                self.win_animation_ongoing = True
                self.ui.win_text_angle = random.randint(-4, 4)

    def input(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE] and self.can_toggle and self.currPlayer.balance >= self.currPlayer.bet_size:
            self.toggle_spinning()
            self.spin_time = pygame.time.get_ticks()
            self.currPlayer.place_bet()
            self.machine_balance += self.currPlayer.bet_size
            self.currPlayer.last_payout = None


    def draw_reels(self, delta_time):
        for reel in self.reel_list:
            self.reel_list[reel].animate(delta_time)

    def spawn_reels(self):
        if not self.reel_list:
            x_topleft, y_topleft = 10, -300
            while self.reel_index < 3:
                if self.reel_index > 0:
                    x_topleft, y_topleft = x_topleft + (300 + X_OFFSET), y_topleft
                self.reel_list[self.reel_index] = Reel((x_topleft, y_topleft))
                self.reel_index += 1

    def toggle_spinning(self):
        if self.can_toggle:
            self.spin_time = pygame.time.get_ticks()
            self.spinning = not self.spinning
            self.can_toggle = False
            for reel in self.reel_list.values():
                reel.start_spin(0)
            self.win_animation_ongoing = False

    def get_result(self):
        for reel in self.reel_list:
            self.spin_result[reel] = self.reel_list[reel].reel_spin_result()
        return self.spin_result

    def check_wins(self, result):
        hits = {}
        horizontal = flip_horizontal(result)
        for row in horizontal:
            for sym in row:
                if row.count(sym) > 2:
                    possible_win = [idx for idx, val in enumerate(row) if sym == val]
                    if len(longest_seq(possible_win)) > 2:
                        hits[horizontal.index(row) + 1] = [sym, longest_seq(possible_win), symbols_values[sym]]
        if hits:
            self.can_animate = True
        return hits

    def pay_player(self, win_data, curr_player):
        total_win = 0
        for v in win_data.values():
            total_win += v[2] * len(v[1])
        curr_player.balance += total_win
        self.machine_balance -= total_win
        curr_player.last_payout = total_win
        curr_player.total_won += total_win

    def play_win_sound(self, win_data):
        sum = 0
        for item in win_data.values():
            sum += len(item[1])
        if sum == 3:
            self.win_three.play()

    def win_animation(self):
        if self.win_animation_ongoing and self.win_data:
            for k, v in list(self.win_data.items()):
                if k == 1:
                    animationRow = 3
                elif k == 3:
                    animationRow = 1
                else:
                    animationRow = 2
                animationCols = v[1]
                for reel in self.reel_list:
                    if reel in animationCols and self.can_animate:
                        self.reel_list[reel].symbol_list.sprites()[animationRow].fade_in = True
                    for symbol in self.reel_list[reel].symbol_list:
                        if not symbol.fade_in:
                            symbol.fade_out = True

    def update(self, delta_time):
        self.cooldowns()
        self.input()
        self.draw_reels(delta_time)
        for reel in self.reel_list:
            self.reel_list[reel].symbol_list.draw(self.display_surface)
            self.reel_list[reel].symbol_list.update()
        self.ui.update()
        self.win_animation()