import time
import math
import sys
import tty
import termios
import threading
from pathlib import Path
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306

# Function to read a single keypress without blocking
def getch():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

# Thread for keyboard input
def keyboard_input_thread(animator):
    print("Keyboard controls:")
    print("1: Blink animation")
    print("2: Thinking animation")
    print("3: Surprised animation")
    print("4: Looking around animation")
    print("q: Quit")

    while True:
        key = getch()
        if key == '1':
            animator.set_animation("blink")
            print("Changed to blink animation")
        elif key == '2':
            animator.set_animation("thinking")
            print("Changed to thinking animation")
        elif key == '3':
            animator.set_animation("surprised")
            print("Changed to surprised animation")
        elif key == '4':
            animator.set_animation("looking")
            print("Changed to looking around animation")
        elif key == 'q':
            print("Quitting...")
            animator.running = False
            break

class OLEDEyeAnimator:
    def __init__(self, device):
        # Store the OLED device
        self.device = device

        # Screen dimensions
        self.SCREEN_WIDTH = device.width
        self.SCREEN_HEIGHT = device.height

        # Eye parameters
        self.eye_y_pos = self.SCREEN_HEIGHT // 2
        self.eye_spacing = 40  # Distance between eye centers
        self.left_eye_x = self.SCREEN_WIDTH // 2 - self.eye_spacing // 2
        self.right_eye_x = self.SCREEN_WIDTH // 2 + self.eye_spacing // 2

        # Eye dimensions
        self.open_width = 20
        self.open_height = 35
        self.open_radius = 5
        self.closed_width = 22
        self.closed_line_thickness = 2

        # Animation state
        self.current_animation = "blink"
        self.animation_start_time = time.time()
        self.running = True

    def draw_open_eyes(self, draw):
        """Draw open eyes (rounded squares)"""
        left_x0 = self.left_eye_x - self.open_width // 2
        left_y0 = self.eye_y_pos - self.open_height // 2
        left_x1 = self.left_eye_x + self.open_width // 2
        left_y1 = self.eye_y_pos + self.open_height // 2

        right_x0 = self.right_eye_x - self.open_width // 2
        right_y0 = self.eye_y_pos - self.open_height // 2
        right_x1 = self.right_eye_x + self.open_width // 2
        right_y1 = self.eye_y_pos + self.open_height // 2

        try:
            # Use rounded_rectangle if available
            draw.rounded_rectangle([(left_x0, left_y0), (left_x1, left_y1)], 
                                  radius=self.open_radius, outline=1, fill=1)
            draw.rounded_rectangle([(right_x0, right_y0), (right_x1, right_y1)], 
                                  radius=self.open_radius, outline=1, fill=1)
        except AttributeError:
            # Fallback for older Pillow versions
            draw.rectangle([(left_x0, left_y0), (left_x1, left_y1)], outline=1, fill=1)
            draw.rectangle([(right_x0, right_y0), (right_x1, right_y1)], outline=1, fill=1)

    def draw_closed_eyes(self, draw):
        """Draw closed eyes (horizontal lines)"""
        line_y = self.eye_y_pos
        left_x_start = self.left_eye_x - self.closed_width // 2
        left_x_end = self.left_eye_x + self.closed_width // 2
        right_x_start = self.right_eye_x - self.closed_width // 2
        right_x_end = self.right_eye_x + self.closed_width // 2

        draw.line([(left_x_start, line_y), (left_x_end, line_y)], 
                 fill=1, width=self.closed_line_thickness)
        draw.line([(right_x_start, line_y), (right_x_end, line_y)], 
                 fill=1, width=self.closed_line_thickness)

    def draw_squinting_eyes(self, draw):
        """Draw squinting eyes (smaller rounded rectangles)"""
        squint_height = self.open_height // 2

        left_x0 = self.left_eye_x - self.open_width // 2
        left_y0 = self.eye_y_pos - squint_height // 2
        left_x1 = self.left_eye_x + self.open_width // 2
        left_y1 = self.eye_y_pos + squint_height // 2

        right_x0 = self.right_eye_x - self.open_width // 2
        right_y0 = self.eye_y_pos - squint_height // 2
        right_x1 = self.right_eye_x + self.open_width // 2
        right_y1 = self.eye_y_pos + squint_height // 2

        try:
            # Use rounded_rectangle if available
            draw.rounded_rectangle([(left_x0, left_y0), (left_x1, left_y1)], 
                                  radius=3, outline=1, fill=1)
            draw.rounded_rectangle([(right_x0, right_y0), (right_x1, right_y1)], 
                                  radius=3, outline=1, fill=1)
        except AttributeError:
            # Fallback for older Pillow versions
            draw.rectangle([(left_x0, left_y0), (left_x1, left_y1)], outline=1, fill=1)
            draw.rectangle([(right_x0, right_y0), (right_x1, right_y1)], outline=1, fill=1)

    def draw_surprised_eyes(self, draw):
        """Draw surprised eyes (larger circles)"""
        radius = int(self.open_height // 1.5)
        draw.ellipse((self.left_eye_x - radius, self.eye_y_pos - radius, 
                     self.left_eye_x + radius, self.eye_y_pos + radius), outline=1, fill=1)
        draw.ellipse((self.right_eye_x - radius, self.eye_y_pos - radius, 
                     self.right_eye_x + radius, self.eye_y_pos + radius), outline=1, fill=1)

    def draw_looking_eyes(self, draw, look_x_offset=0, look_y_offset=0):
        """Draw eyes with pupils looking in a specific direction"""
        # Draw the eye whites (same as open eyes)
        left_x0 = self.left_eye_x - self.open_width // 2
        left_y0 = self.eye_y_pos - self.open_height // 2
        left_x1 = self.left_eye_x + self.open_width // 2
        left_y1 = self.eye_y_pos + self.open_height // 2

        right_x0 = self.right_eye_x - self.open_width // 2
        right_y0 = self.eye_y_pos - self.open_height // 2
        right_x1 = self.right_eye_x + self.open_width // 2
        right_y1 = self.eye_y_pos + self.open_height // 2

        try:
            # Use rounded_rectangle if available
            draw.rounded_rectangle([(left_x0, left_y0), (left_x1, left_y1)], 
                                  radius=self.open_radius, outline=1, fill=1)
            draw.rounded_rectangle([(right_x0, right_y0), (right_x1, right_y1)], 
                                  radius=self.open_radius, outline=1, fill=1)
        except AttributeError:
            # Fallback for older Pillow versions
            draw.rectangle([(left_x0, left_y0), (left_x1, left_y1)], outline=1, fill=1)
            draw.rectangle([(right_x0, right_y0), (right_x1, right_y1)], outline=1, fill=1)

        # Calculate pupil positions
        pupil_radius = 6
        max_offset_x = (self.open_width // 2) - pupil_radius - 1
        max_offset_y = (self.open_height // 2) - pupil_radius - 1

        # Apply the offsets (clamped to stay within the eye)
        pupil_x_offset = int(look_x_offset * max_offset_x)
        pupil_y_offset = int(look_y_offset * max_offset_y)

        # Draw the pupils (black circles inside the white eyes)
        left_pupil_x = self.left_eye_x + pupil_x_offset
        left_pupil_y = self.eye_y_pos + pupil_y_offset
        right_pupil_x = self.right_eye_x + pupil_x_offset
        right_pupil_y = self.eye_y_pos + pupil_y_offset

        # For OLED, we need to "erase" the pupils by drawing black circles
        # This is done by setting fill=0 to create black circles in the white eyes
        draw.ellipse((left_pupil_x - pupil_radius, left_pupil_y - pupil_radius,
                     left_pupil_x + pupil_radius, left_pupil_y + pupil_radius), outline=0, fill=0)
        draw.ellipse((right_pupil_x - pupil_radius, right_pupil_y - pupil_radius,
                     right_pupil_x + pupil_radius, right_pupil_y + pupil_radius), outline=0, fill=0)

    # Animation sequences
    def animate_looking_around(self, elapsed_time):
        """Animation for eyes looking around in a pattern"""
        # Define a complete look-around cycle (in seconds)
        CYCLE_TIME = 3.0

        # Calculate normalized time within the cycle (0.0 to 1.0)
        cycle_position = (elapsed_time % CYCLE_TIME) / CYCLE_TIME

        # Define a pattern for looking around
        # This creates a circular pattern
        look_x = 0.8 * math.cos(cycle_position * 2 * math.pi)
        look_y = 0.8 * math.sin(cycle_position * 2 * math.pi)

        # Draw the eyes with the calculated look direction
        with canvas(self.device) as draw:
            self.draw_looking_eyes(draw, look_x, look_y)

    def animate_blink(self, elapsed_time):
        """Blink animation sequence"""
        TIME_OPEN = 1.0
        TIME_CLOSED = 0.5
        total_cycle = TIME_OPEN + TIME_CLOSED
        cycle_time = elapsed_time % total_cycle

        with canvas(self.device) as draw:
            if cycle_time < TIME_OPEN:
                self.draw_open_eyes(draw)
            else:
                self.draw_closed_eyes(draw)

    def animate_thinking(self, elapsed_time):
        """Thinking animation (squinting and normal)"""
        TIME_NORMAL = 0.5
        TIME_SQUINT = 1.0
        total_cycle = TIME_NORMAL + TIME_SQUINT
        cycle_time = elapsed_time % total_cycle

        with canvas(self.device) as draw:
            if cycle_time < TIME_NORMAL:
                self.draw_open_eyes(draw)
            else:
                self.draw_squinting_eyes(draw)

    def animate_surprised(self, elapsed_time):
        """Surprised animation (wide eyes then normal)"""
        TIME_SURPRISED = 1.0
        TIME_NORMAL = 0.5
        total_cycle = TIME_SURPRISED + TIME_NORMAL
        cycle_time = elapsed_time % total_cycle

        with canvas(self.device) as draw:
            if cycle_time < TIME_SURPRISED:
                self.draw_surprised_eyes(draw)
            else:
                self.draw_open_eyes(draw)

    def set_animation(self, animation_name):
        """Set the current animation"""
        self.current_animation = animation_name
        self.animation_start_time = time.time()

    def run(self):
        """Main animation loop"""
        animations = {
            "blink": self.animate_blink,
            "thinking": self.animate_thinking,
            "surprised": self.animate_surprised,
            "looking": self.animate_looking_around,
        }

        # Default animation
        if not self.current_animation:
            self.set_animation("blink")

        # Start keyboard input thread
        input_thread = threading.Thread(target=keyboard_input_thread, args=(self,))
        input_thread.daemon = True
        input_thread.start()

        try:
            while self.running:
                # Calculate elapsed time for current animation
                elapsed_time = time.time() - self.animation_start_time

                # Run current animation
                animations[self.current_animation](elapsed_time)

                # Small delay to prevent high CPU usage
                time.sleep(0.02)

        except KeyboardInterrupt:
            print(" Animation stopped by Ctrl+C.")
            self.running = False

# Main function to initialize and run the OLED eye animator
def main():
    try:
        # Initialize I2C interface
        serial = i2c(port=1, address=0x3C)  # Check address with i2cdetect -y 1
        # Initialize OLED device
        device = ssd1306(serial)
        print("OLED display initialized successfully.")

        # Create and run the eye animator
        animator = OLEDEyeAnimator(device)
        print("Starting OLED eye animations...")
        print("Press Ctrl+C to exit.")
        animator.run()

    except Exception as e:
        print(f"Error: {e}")
        print("Ensure I2C is enabled and the display is connected correctly.")
    finally:
        # Clean up display on exit
        try:
            device.cleanup()
            print("OLED display cleaned up.")
        except:
            pass

if __name__ == "__main__":
    main()
