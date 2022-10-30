from picographics import PicoGraphics, DISPLAY_INKY_PACK
import qrcode


class StatusDisplay():
    
    def __init__(self):
        self.display = PicoGraphics(display=DISPLAY_INKY_PACK)
        # you can change the update speed here!
        # it goes from 0 (slowest) to 3 (fastest)
        self.display.set_update_speed(2)
        self.width, self.height = self.display.get_bounds()

        
    def clear_display(self):
        self.display.set_pen(15)
        self.display.clear()
        
        
    def draw_boot(self,boot_state='booting..'):
        self.display.set_font("bitmap8")
        self.clear_display()
        self.display.set_pen(0)
        self.display.text("Inky Status is booting....", 10, 10, scale=2)
        self.display.text("Status: {0}".format(boot_state), 10, 40, wordwrap=self.width-20, scale=2)
        self.display.update()
        
    def draw_status(self, status_message, update_time):
        self.display.set_font("bitmap8")
        self.clear_display()
        self.display.set_pen(0)
        self.display.text("James is currently:", 10, 10, scale=2)
        self.display.text(status_message, 10, 40, wordwrap=self.width-20, scale=2)
        self.display.text(f'Updated: {update_time}', 10, 120, scale=1)
        self.display.update()
        
        

    def measure_qr_code(self, size, code):
        w, h = code.get_size()
        module_size = int(size / w)
        return int(module_size * w), module_size

    def draw_qr_code(self, ox, oy, size, code):
        size, module_size = self.measure_qr_code(size, code)
        self.display.set_pen(15)
        self.display.rectangle(ox, oy, size, size)
        self.display.set_pen(0)
        for x in range(size):
            for y in range(size):
                if code.get_module(x, y):
                    self.display.rectangle(ox + x * module_size, oy + y * module_size, module_size, module_size)
                    
            
            
    def draw_ssid_screen(self, ssid_string, ssid):
        self.clear_display()
        code = qrcode.QRCode()
        code.set_text(ssid_string)
        size, _ = self.measure_qr_code(128, code)
        left = top = int((128/2)-(size/2))
        self.draw_qr_code(left, top, 128, code)
        
        self.display.set_pen(0)
        self.display.text(f"Connect to hotspot: {ssid}", 134, 0, 120, 2)
        self.display.update()
                
        
