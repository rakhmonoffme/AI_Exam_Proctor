import pyperclip
import time
from pynput import keyboard
import threading

class ScreenActivityMonitor:
    def __init__(self):
        """Initialize Screen Activity Monitor"""
        self.is_monitoring = False
        self.last_clipboard = ""
        self.tab_switches = 0
        self.copy_paste_events = 0
        
        # Track keyboard events
        self.ctrl_pressed = False
        self.alt_pressed = False
        self.cmd_pressed = False
        
        # Results storage
        self.events = []
        
        # Keyboard listener
        self.keyboard_listener = None
    
    def _on_key_press(self, key):
        """Handle key press events"""
        try:
            # Track modifier keys
            if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                self.ctrl_pressed = True
            elif key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
                self.alt_pressed = True
            elif key == keyboard.Key.cmd:
                self.cmd_pressed = True
            
            # Detect Alt+Tab (Windows/Linux)
            if self.alt_pressed and key == keyboard.Key.tab:
                self.tab_switches += 1
                self._log_event("tab_switch", "Alt+Tab detected")
            
            # Detect Cmd+Tab (Mac)
            if self.cmd_pressed and key == keyboard.Key.tab:
                self.tab_switches += 1
                self._log_event("tab_switch", "Cmd+Tab detected")
            
            # Detect Ctrl+C (Copy)
            if self.ctrl_pressed and hasattr(key, 'char') and key.char == 'c':
                self.copy_paste_events += 1
                self._log_event("copy", "Ctrl+C detected")
            
            # Detect Ctrl+V (Paste)
            if self.ctrl_pressed and hasattr(key, 'char') and key.char == 'v':
                self.copy_paste_events += 1
                self._log_event("paste", "Ctrl+V detected")
            
            # Detect Cmd+C (Mac)
            if self.cmd_pressed and hasattr(key, 'char') and key.char == 'c':
                self.copy_paste_events += 1
                self._log_event("copy", "Cmd+C detected")
            
            # Detect Cmd+V (Mac)
            if self.cmd_pressed and hasattr(key, 'char') and key.char == 'v':
                self.copy_paste_events += 1
                self._log_event("paste", "Cmd+V detected")
                
        except AttributeError:
            pass
    
    def _on_key_release(self, key):
        """Handle key release events"""
        try:
            if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                self.ctrl_pressed = False
            elif key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
                self.alt_pressed = False
            elif key == keyboard.Key.cmd:
                self.cmd_pressed = False
        except AttributeError:
            pass
    
    def _monitor_clipboard(self):
        """Monitor clipboard changes in background"""
        while self.is_monitoring:
            try:
                current_clipboard = pyperclip.paste()
                if current_clipboard != self.last_clipboard and self.last_clipboard != "":
                    self.copy_paste_events += 1
                    self._log_event("clipboard_change", "Clipboard content changed")
                self.last_clipboard = current_clipboard
            except Exception:
                pass
            time.sleep(0.5)
    
    def _log_event(self, event_type, description):
        """Log an event"""
        event = {
            'type': event_type,
            'description': description,
            'timestamp': time.time()
        }
        self.events.append(event)
        print(f"[{event_type.upper()}] {description}")
    
    def start_monitoring(self, duration=None):
        """
        Start monitoring screen activity
        
        Args:
            duration: Monitoring duration in seconds (None for indefinite)
            
        Returns:
            dict: Monitoring results
        """
        print("Starting screen activity monitoring...")
        
        self.is_monitoring = True
        self.tab_switches = 0
        self.copy_paste_events = 0
        self.events = []
        
        # Get initial clipboard state
        try:
            self.last_clipboard = pyperclip.paste()
        except:
            self.last_clipboard = ""
        
        # Start clipboard monitoring thread
        clipboard_thread = threading.Thread(target=self._monitor_clipboard, daemon=True)
        clipboard_thread.start()
        
        # Start keyboard listener
        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        self.keyboard_listener.start()
        
        # Monitor for specified duration
        if duration:
            print(f"Monitoring for {duration} seconds...")
            time.sleep(duration)
            return self.stop_monitoring()
        else:
            print("Monitoring started (call stop_monitoring() to end)")
    
    def stop_monitoring(self):
        """
        Stop monitoring and return results
        
        Returns:
            dict: Activity summary
        """
        print("Stopping screen activity monitoring...")
        
        self.is_monitoring = False
        
        if self.keyboard_listener:
            self.keyboard_listener.stop()
        
        results = {
            'tab_switches': self.tab_switches,
            'copy_paste_events': self.copy_paste_events,
            'total_events': len(self.events),
            'events': self.events,
            'suspicious_activity': self.tab_switches > 5 or self.copy_paste_events > 10
        }
        
        print(f"\nMonitoring Summary:")
        print(f"Tab Switches: {results['tab_switches']}")
        print(f"Copy/Paste Events: {results['copy_paste_events']}")
        print(f"Suspicious Activity: {results['suspicious_activity']}")
        
        return results
    
    def get_current_stats(self):
        """
        Get current monitoring statistics without stopping
        
        Returns:
            dict: Current stats
        """
        return {
            'tab_switches': self.tab_switches,
            'copy_paste_events': self.copy_paste_events,
            'total_events': len(self.events),
            'is_monitoring': self.is_monitoring
        }


# Example usage
if __name__ == "__main__":
    # Using class
    monitor = ScreenActivityMonitor()
    
    # Method 1: Monitor for specific duration
    # results = monitor.start_monitoring(duration=30)
    
    # Method 2: Start/stop manually
    # monitor.start_monitoring()
    # # ... do other things ...
    # time.sleep(30)
    # results = monitor.stop_monitoring()
    
    # Method 3: Get stats while monitoring
    monitor.start_monitoring()
    # time.sleep(30)
    stats = monitor.get_current_stats()
    print(stats)
    # monitor.stop_monitoring()
    