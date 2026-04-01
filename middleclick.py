import os
import sys
import time
import ctypes
import math
from ctypes import CFUNCTYPE, POINTER, Structure, c_float, c_int, c_double, c_void_p, c_uint32, c_bool

# --- 1. Load System Frameworks ---

try:
    mt = ctypes.CDLL("/System/Library/PrivateFrameworks/MultitouchSupport.framework/MultitouchSupport")
    cg = ctypes.CDLL("/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics")
    ax = ctypes.CDLL("/System/Library/Frameworks/ApplicationServices.framework/Frameworks/HIServices.framework/HIServices") 
except Exception as e:
    print(f"Error: Could not load required frameworks: {e}")
    sys.exit(1)

# --- 2. Define Types ---

class CGPoint(Structure):
    _fields_ = [("x", c_double), ("y", c_double)]

class MTContact(Structure):
    _fields_ = [
        ("frame", c_int), ("timestamp", c_double), ("identifier", c_int),
        ("state", c_int), ("finger", c_int), ("hand", c_int),
        ("normalizedX", c_float), ("normalizedY", c_float),
        ("positionX", c_float), ("positionY", c_float),
        ("velocityX", c_float), ("velocityY", c_float),
        ("diameterX", c_float), ("diameterY", c_float),
        ("orientation", c_float), ("ellipseMajor", c_float),
        ("ellipseMinor", c_float), ("aspect", c_float),
        ("area", c_float), ("unknown1", c_int),
    ]

MTDeviceRef = c_void_p
MTContactFrameCallback = CFUNCTYPE(c_int, MTDeviceRef, POINTER(MTContact), c_int, c_double, c_int)

# --- 3. Signatures ---

mt.MTDeviceCreateDefault.restype = MTDeviceRef
mt.MTDeviceCreateDefault.argtypes = []
mt.MTRegisterContactFrameCallback.restype = None
mt.MTRegisterContactFrameCallback.argtypes = [MTDeviceRef, MTContactFrameCallback]
mt.MTDeviceStart.restype = None
mt.MTDeviceStart.argtypes = [MTDeviceRef, c_int]

cg.CGEventCreate.argtypes = [c_void_p]
cg.CGEventCreate.restype = c_void_p
cg.CGEventGetLocation.argtypes = [c_void_p]
cg.CGEventGetLocation.restype = CGPoint
cg.CGEventCreateMouseEvent.argtypes = [c_void_p, c_uint32, CGPoint, c_uint32]
cg.CGEventCreateMouseEvent.restype = c_void_p
cg.CGEventPost.argtypes = [c_uint32, c_void_p]
cg.CGEventPost.restype = None
cg.CFRelease.argtypes = [c_void_p]
cg.CFRelease.restype = None
ax.AXIsProcessTrusted.argtypes = []
ax.AXIsProcessTrusted.restype = c_bool

# Constants
kCGEventOtherMouseDown = 25
kCGEventOtherMouseUp = 26
kCGMouseButtonCenter = 2
kCGHIDEventTap = 0

# --- 4. Gesture Handler (Tap-to-Release with Movement Filter) ---

class GestureHandler:
    def __init__(self):
        self.session_active = False
        self.start_time = 0
        self.start_positions = {}
        self.is_swipe = False
        self.session_finger_count = 0
        
        # Heuristics
        self.max_tap_duration = 0.3  # 300ms max for a tap
        self.swipe_threshold = 0.04 # Normalized distance threshold for a swipe

    def handle_contacts(self, contacts_ptr, count):
        if count > 0:
            if not self.session_active:
                # Start Session
                self.session_active = True
                self.start_time = time.time()
                self.is_swipe = False
                self.session_finger_count = count
                # Store starting positions
                self.start_positions = {}
                for i in range(count):
                    c = contacts_ptr[i]
                    self.start_positions[c.identifier] = (c.normalizedX, c.normalizedY)
            else:
                # Track maximum fingers seen in session
                if count > self.session_finger_count:
                    self.session_finger_count = count
                
                # Check for movement (swipe detection)
                if not self.is_swipe:
                    for i in range(count):
                        c = contacts_ptr[i]
                        if c.identifier in self.start_positions:
                            sx, sy = self.start_positions[c.identifier]
                            dist = math.sqrt((c.normalizedX - sx)**2 + (c.normalizedY - sy)**2)
                            if dist > self.swipe_threshold:
                                self.is_swipe = True
                                break
        else:
            # All fingers lifted
            if self.session_active:
                duration = time.time() - self.start_time
                # Trigger ONLY if exactly 3 fingers were used, it wasn't a swipe, and it was quick
                if self.session_finger_count == 3 and not self.is_swipe and duration < self.max_tap_duration:
                    self.trigger_middle_click()
                
                # Reset Session
                self.session_active = False
                self.session_finger_count = 0

    def trigger_middle_click(self):
        dummy = cg.CGEventCreate(None)
        if not dummy: return
        location = cg.CGEventGetLocation(dummy)
        cg.CFRelease(dummy)
        
        down = cg.CGEventCreateMouseEvent(None, kCGEventOtherMouseDown, location, kCGMouseButtonCenter)
        up = cg.CGEventCreateMouseEvent(None, kCGEventOtherMouseUp, location, kCGMouseButtonCenter)
        
        if down and up:
            cg.CGEventPost(kCGHIDEventTap, down)
            cg.CGEventPost(kCGHIDEventTap, up)
            cg.CFRelease(down)
            cg.CFRelease(up)
            print(f"[{time.strftime('%H:%M:%S')}] Middle Tap Detected (Release-based)")

handler = GestureHandler()

@MTContactFrameCallback
def callback(device, contacts, count, timestamp, frame):
    handler.handle_contacts(contacts, count)
    return 0

# --- 5. Main ---

print("--- MiddleTap for macOS (Tap-to-Release Mode) ---")
print("Detection: Trigger on release | Filter: No swipe allowed")

if not ax.AXIsProcessTrusted():
    print("ACTION REQUIRED: Accessibility permissions missing.")

device = mt.MTDeviceCreateDefault()
if not device:
    print("Error: No trackpad found.")
    sys.exit(1)

_callback_ref = callback # Prevent GC
mt.MTRegisterContactFrameCallback(device, _callback_ref)
mt.MTDeviceStart(device, 0)

print("Running. Tap and lift 3 fingers quickly to middle-click.")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nQuitting...")
