import time
import random
import board
from analogio import AnalogIn
from adafruit_circuitplayground import cp

class SimonGame:
    FAILURE_TONE = 100
    BASE_SEQUENCE_DELAY = 0.5
    GUESS_TIMEOUT = 3.0
    DEBOUNCE = 0.125  # Controls button debounce time
    BUTTON_FEEDBACK_DURATION = 0.10  # Controls how long button feedback plays
    SPEED_INCREMENT = 0.035  # speed up per round
    MIN_DURATION = 0.1
    SEQUENCE_LENGTH = {1: 5, 2: 8, 3: 10, 4: 15}
    SIMON_BUTTONS = {
        1: {'pads': (4, 5), 'pixels': (0, 1, 2), 'color': 0x00FF00, 'freq': 415},
        2: {'pads': (6, 7), 'pixels': (2, 3, 4), 'color': 0xFFFF00, 'freq': 252},
        3: {'pads': (0, 1), 'pixels': (5, 6, 7), 'color': 0x0000FF, 'freq': 209},
        4: {'pads': (2, 3), 'pixels': (7, 8, 9), 'color': 0xFF0000, 'freq': 310},
    }

    def __init__(self):
        self.sequence = []
        self.current_step = 1
        self.sequence_speed = 0.5
        self.skill_level = 1
        self.reset_game()

    def reset_game(self):
        cp.pixels.fill(0)
        cp.pixels[0] = 0xFFFFFF
        self.skill_level = self.choose_skill_level()
        self.sequence = self.generate_sequence(self.skill_level)
        self.current_step = 1
        self.sequence_speed = 0.42

    def choose_skill_level(self):
        skill_level = 1
        while not cp.button_b:
            if cp.button_a:
                skill_level = skill_level + 1 if skill_level < 4 else 1
                cp.pixels.fill(0)
                for p in range(skill_level):
                    cp.pixels[p] = 0xFFFFFF
                freq = 200 + (skill_level - 1) * 100  # 200, 300, 400, 500 Hz
                cp.play_tone(freq, 0.1)  # Play tone only when A is pressed
                time.sleep(self.DEBOUNCE)
        return skill_level

    def generate_random_seed(self):
        # Generate a new random seed safely using the analog inputs
        try:
            with AnalogIn(board.A4) as a4, AnalogIn(board.A5) as a5, AnalogIn(board.A6) as a6:
                seed = a4.value + a5.value + a6.value
                random.seed(seed)
        except Exception:
            # Fallback to using the current time as seed if analog inputs fail
            random.seed(int(time.monotonic() * 1000))

    def generate_sequence(self, skill_level):
        # Generate a new random seed first
        self.generate_random_seed()
        # Then create a new random sequence
        return [random.randint(1, 4) for _ in range(self.SEQUENCE_LENGTH[skill_level])]

    def new_game(self, skill_level):
        # This method is now deprecated but kept for backward compatibility
        return self.generate_sequence(skill_level)

    def indicate_button(self, button, duration):
        cp.pixels.fill(0)
        for p in button['pixels']:
            cp.pixels[p] = button['color']
        if button['freq']:
            cp.play_tone(button['freq'], duration)
        else:
            time.sleep(duration)
        cp.pixels.fill(0)

    def show_sequence(self):
        for i in range(self.current_step):
            time.sleep(0.05)
            self.indicate_button(self.SIMON_BUTTONS[self.sequence[i]], self.sequence_speed)

    def cap_map(self, b):
        return {
            1: cp.touch_A1, 2: cp.touch_A2, 3: cp.touch_A3, 4: cp.touch_A4,
            5: cp.touch_A5, 6: cp.touch_A6, 7: cp.touch_TX
        }.get(b, None)

    def get_button_press(self):
        for button in self.SIMON_BUTTONS.values():
            for pad in button['pads']:
                if self.cap_map(pad):
                    self.indicate_button(button, self.BUTTON_FEEDBACK_DURATION)
                    return button
        return None

    def game_lost(self):
        cp.pixels.fill(0)
        for p in self.SIMON_BUTTONS[self.sequence[self.current_step - 1]]['pixels']:
            cp.pixels[p] = self.SIMON_BUTTONS[self.sequence[self.current_step - 1]]['color']
        cp.play_tone(self.FAILURE_TONE, 1.5)
        time.sleep(1)
        self.reset_game()

    def game_won(self):
        order = [4, 2, 3, 1]
        for _ in range(3):
            for b in order:
                self.indicate_button(self.SIMON_BUTTONS[b], 0.1)
        for b in [4, 2]:
            self.indicate_button(self.SIMON_BUTTONS[b], 0.1)
        time.sleep(1)
        self.reset_game()

    def run(self):
        while True:
            self.show_sequence()
            for i in range(self.current_step):
                start_time = time.monotonic()
                guess = None
                while time.monotonic() - start_time < self.GUESS_TIMEOUT and guess is None:
                    guess = self.get_button_press()
                if guess != self.SIMON_BUTTONS[self.sequence[i]]:
                    self.game_lost()
                    break
            else:
                self.current_step += 1
                self.sequence_speed = max(self.sequence_speed - self.SPEED_INCREMENT, self.MIN_DURATION)
                if self.current_step > len(self.sequence):
                    self.game_won()
            time.sleep(self.BASE_SEQUENCE_DELAY)


# Run the game
game = SimonGame()
game.run()
