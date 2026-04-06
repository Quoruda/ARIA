import sys
import pygame
import ctypes
from ctypes import util

class WindowManager:
    """Handles cross-platform borderless window movement for Pygame."""
    def __init__(self):
        self.os_type = sys.platform
        self.x11 = None
        self.display = None
        self.root_win = None
        self.window_handle = None
        self.user32 = None
        self.xshape = None
        
        self.setup()

    def setup(self):
        try:
            # Get common window handle from Pygame
            wm_info = pygame.display.get_wm_info()
            self.window_handle = wm_info.get('window')

            if self.os_type.startswith('linux'):
                # Linux/X11 Setup
                x11_path = util.find_library('X11')
                if x11_path:
                    self.x11 = ctypes.CDLL(x11_path)
                    self.x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
                    self.x11.XOpenDisplay.restype = ctypes.c_void_p
                    self.display = self.x11.XOpenDisplay(None)
                    if self.display:
                        self.x11.XDefaultRootWindow.argtypes = [ctypes.c_void_p]
                        self.x11.XDefaultRootWindow.restype = ctypes.c_ulong
                        self.root_win = self.x11.XDefaultRootWindow(self.display)
                        
                        # XShape Extension Setup
                        xshape_path = util.find_library('Xext')
                        if xshape_path:
                            self.xshape = ctypes.CDLL(xshape_path)
                            self.xshape.XShapeCombineRectangles.argtypes = [
                                ctypes.c_void_p, ctypes.c_ulong, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int
                            ]
                        
                        # Fix XFlush argtypes to avoid pointer truncation segfault
                        self.x11.XFlush.argtypes = [ctypes.c_void_p]
            
            elif self.os_type == 'win32':
                # Windows Setup
                self.user32 = ctypes.windll.user32
                
        except Exception as e:
            print(f"WindowManager setup failed: {e}")

    def get_global_mouse_pos(self):
        """Returns (x, y) global screen coordinates."""
        if self.os_type.startswith('linux') and self.x11 and self.display:
            self.x11.XQueryPointer.argtypes = [
                ctypes.c_void_p, ctypes.c_ulong,
                ctypes.POINTER(ctypes.c_ulong), ctypes.POINTER(ctypes.c_ulong),
                ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int),
                ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int),
                ctypes.POINTER(ctypes.c_uint)
            ]
            root_ret, child_ret = ctypes.c_ulong(), ctypes.c_ulong()
            root_x, root_y = ctypes.c_int(), ctypes.c_int()
            win_x, win_y = ctypes.c_int(), ctypes.c_int()
            mask = ctypes.c_uint()
            self.x11.XQueryPointer(self.display, self.root_win, 
                                 ctypes.byref(root_ret), ctypes.byref(child_ret),
                                 ctypes.byref(root_x), ctypes.byref(root_y),
                                 ctypes.byref(win_x), ctypes.byref(win_y),
                                 ctypes.byref(mask))
            return root_x.value, root_y.value
        
        elif self.os_type == 'win32' and self.user32:
            class POINT(ctypes.Structure):
                _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
            pt = POINT()
            self.user32.GetCursorPos(ctypes.byref(pt))
            return pt.x, pt.y
        
        # Fallback to relative (will be buggy for window moving)
        return pygame.mouse.get_pos()

    def move_window(self, x, y):
        """Moves the window to (x, y) global coordinates."""
        if not self.window_handle:
            wm_info = pygame.display.get_wm_info()
            self.window_handle = wm_info.get('window')

        if self.os_type.startswith('linux') and self.x11 and self.display and self.window_handle:
            self.x11.XMoveWindow.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_int, ctypes.c_int]
            self.x11.XMoveWindow(self.display, self.window_handle, int(x), int(y))
            self.x11.XFlush.argtypes = [ctypes.c_void_p]
            self.x11.XFlush(self.display)
        
        elif self.os_type == 'win32' and self.user32 and self.window_handle:
            # SWP_NOSIZE = 0x0001, SWP_NOZORDER = 0x0004
            self.user32.SetWindowPos(self.window_handle, 0, int(x), int(y), 0, 0, 0x0001 | 0x0004)

    def enable_transparency(self, color):
        """Makes the specified RGBA color transparent for the window."""
        if not self.window_handle:
            wm_info = pygame.display.get_wm_info()
            self.window_handle = wm_info.get('window')

        if self.os_type == 'win32' and self.user32 and self.window_handle:
            hwnd = self.window_handle
            style = self.user32.GetWindowLongW(hwnd, -20)
            self.user32.SetWindowLongW(hwnd, -20, style | 0x80000)
            # Use BGR for Windows COLORREF, ignore alpha for LWA_COLORKEY
            color_ref = (color[2] << 16) | (color[1] << 8) | color[0]
            self.user32.SetLayeredWindowAttributes(hwnd, color_ref, 0, 0x1)
        
        elif self.os_type.startswith('linux'):
            # Just set colorkey for standard rendering
            pygame.display.get_surface().set_colorkey(color)

    def apply_linux_mask(self, revealed_grid):
        """Uses XShape to 'cut' the window according to the revealed pixels grid."""
        if not (self.x11 and self.display and self.window_handle and self.xshape):
            return
            
        # Create a list of rectangles (one per pixel or per block)
        # Assuming 32x32 grid and 320x320 window
        rect_class = type("XRect", (ctypes.Structure,), {"_fields_": [("x", ctypes.c_short), ("y", ctypes.c_short), ("width", ctypes.c_ushort), ("height", ctypes.c_ushort)]})
        
        rects = []
        scale = 320 // 32 # The scale factor (WINDOW_W / INTERNAL_W)
        
        for y, row in enumerate(revealed_grid):
            for x, revealed in enumerate(row):
                if revealed:
                    r = rect_class()
                    r.x, r.y, r.width, r.height = x * scale, y * scale, scale, scale
                    rects.append(r)
        
        if not rects:
            # Empty mask (make window invisible)
            # We must use at least one empty rect or use ShapeSet with no rects
            self.xshape.XShapeCombineRectangles(self.display, ctypes.c_ulong(self.window_handle), 0, 0, 0, None, 0, 0, 0)
        else:
            rect_array = (rect_class * len(rects))(*rects)
            # ShapeBounding = 0, ShapeClip = 1
            # UNORDERED = 0, YSorted = 1, YXSorted = 2, YXBanded = 3
            # ShapeSet = 0, ShapeUnion = 1, ShapeIntersect = 2, ShapeSubtract = 3, ShapeInvert = 4
            self.xshape.XShapeCombineRectangles(self.display, ctypes.c_ulong(self.window_handle), 0, 0, 0, ctypes.byref(rect_array), len(rects), 0, 3)

        self.x11.XFlush(self.display)

    def close(self):
        if self.os_type.startswith('linux') and self.x11 and self.display:
            self.x11.XCloseDisplay.argtypes = [ctypes.c_void_p]
            self.x11.XCloseDisplay(self.display)
