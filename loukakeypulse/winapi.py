# Copyright (c) 2026 Malek Mzali (Louka). All rights reserved.

import ctypes
import ctypes.wintypes as W


u32 = ctypes.WinDLL("user32", use_last_error=True)
k32 = ctypes.WinDLL("kernel32", use_last_error=True)
dwm = ctypes.WinDLL("dwmapi", use_last_error=True)

ULONG_PTR = ctypes.c_size_t
INJECTED = 0x5350414D


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", W.WORD), ("wScan", W.WORD),
        ("dwFlags", W.DWORD), ("time", W.DWORD),
        ("dwExtraInfo", ULONG_PTR)
    ]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", W.LONG), ("dy", W.LONG),
        ("mouseData", W.DWORD), ("dwFlags", W.DWORD),
        ("time", W.DWORD), ("dwExtraInfo", ULONG_PTR)
    ]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", W.DWORD), ("wParamL", W.WORD), ("wParamH", W.WORD)
    ]


class _IU(ctypes.Union):
    _fields_ = [
        ("ki", KEYBDINPUT), ("mi", MOUSEINPUT), ("hi", HARDWAREINPUT)
    ]


class INPUT(ctypes.Structure):
    _fields_ = [("type", W.DWORD), ("u", _IU)]


u32.SendInput.argtypes = [W.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
u32.SendInput.restype = W.UINT
u32.MapVirtualKeyW.argtypes = [W.UINT, W.UINT]
u32.MapVirtualKeyW.restype = W.UINT
u32.MapVirtualKeyExW.argtypes = [W.UINT, W.UINT, ctypes.c_void_p]
u32.MapVirtualKeyExW.restype = W.UINT
u32.GetKeyboardLayout.argtypes = [W.DWORD]
u32.GetKeyboardLayout.restype = ctypes.c_void_p
u32.GetWindowThreadProcessId.argtypes = [
    ctypes.c_void_p, ctypes.POINTER(W.DWORD)
]
u32.GetWindowThreadProcessId.restype = W.DWORD
u32.GetForegroundWindow.restype = ctypes.c_void_p
u32.ToUnicodeEx.argtypes = [
    W.UINT, W.UINT, ctypes.POINTER(ctypes.c_ubyte),
    W.LPWSTR, ctypes.c_int, W.UINT, ctypes.c_void_p
]
u32.ToUnicodeEx.restype = ctypes.c_int

KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008
MOUSEEVENTF_XDOWN = 0x0080
MOUSEEVENTF_XUP = 0x0100
XBUTTON1 = 0x0001
XBUTTON2 = 0x0002

WH_KEYBOARD_LL = 13
WH_MOUSE_LL = 14

WM_KEYDOWN = 0x100
WM_KEYUP = 0x101
WM_SYSKEYDOWN = 0x104
WM_SYSKEYUP = 0x105
WM_XBUTTONDOWN = 0x20B
WM_XBUTTONUP = 0x20C


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", W.DWORD), ("scanCode", W.DWORD),
        ("flags", W.DWORD), ("time", W.DWORD),
        ("dwExtraInfo", ULONG_PTR)
    ]


class MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("pt", W.POINT), ("mouseData", W.DWORD),
        ("flags", W.DWORD), ("time", W.DWORD),
        ("dwExtraInfo", ULONG_PTR)
    ]


HOOKPROC = ctypes.CFUNCTYPE(
    ctypes.c_ssize_t, ctypes.c_int, W.WPARAM, W.LPARAM
)

u32.CallNextHookEx.argtypes = [
    ctypes.c_void_p, ctypes.c_int, W.WPARAM, W.LPARAM
]
u32.CallNextHookEx.restype = ctypes.c_ssize_t
u32.SetWindowsHookExW.argtypes = [
    ctypes.c_int, HOOKPROC, ctypes.c_void_p, W.DWORD
]
u32.SetWindowsHookExW.restype = ctypes.c_void_p

gdi = ctypes.WinDLL("gdi32", use_last_error=True)
shl = ctypes.WinDLL("shell32", use_last_error=True)

_vp = ctypes.c_void_p

k32.OpenProcess.argtypes = [W.DWORD, W.BOOL, W.DWORD]
k32.OpenProcess.restype = _vp
k32.CloseHandle.argtypes = [_vp]
k32.QueryFullProcessImageNameW.argtypes = [
    _vp, W.DWORD, W.LPWSTR, ctypes.POINTER(W.DWORD)
]
k32.QueryFullProcessImageNameW.restype = W.BOOL

u32.GetDC.argtypes = [_vp]
u32.GetDC.restype = _vp
u32.ReleaseDC.argtypes = [_vp, _vp]
u32.DrawIconEx.argtypes = [
    _vp, ctypes.c_int, ctypes.c_int, _vp,
    ctypes.c_int, ctypes.c_int, W.UINT, _vp, W.UINT
]
u32.DestroyIcon.argtypes = [_vp]

gdi.CreateCompatibleDC.argtypes = [_vp]
gdi.CreateCompatibleDC.restype = _vp
gdi.CreateDIBSection.argtypes = [
    _vp, _vp, W.UINT, ctypes.POINTER(_vp), _vp, W.DWORD
]
gdi.CreateDIBSection.restype = _vp
gdi.SelectObject.argtypes = [_vp, _vp]
gdi.SelectObject.restype = _vp
gdi.DeleteObject.argtypes = [_vp]
gdi.DeleteDC.argtypes = [_vp]

shl.ExtractIconExW.argtypes = [
    W.LPCWSTR, ctypes.c_int, ctypes.POINTER(_vp),
    ctypes.POINTER(_vp), W.UINT
]
shl.ExtractIconExW.restype = W.UINT

winmm = ctypes.WinDLL("winmm")

k32.GetCurrentThread.restype = _vp
k32.SetThreadPriority.argtypes = [_vp, ctypes.c_int]
k32.SetThreadPriority.restype = W.BOOL
k32.CreateEventW.argtypes = [_vp, W.BOOL, W.BOOL, W.LPCWSTR]
k32.CreateEventW.restype = _vp
k32.SetEvent.argtypes = [_vp]
k32.SetEvent.restype = W.BOOL
k32.CreateWaitableTimerExW.argtypes = [_vp, W.LPCWSTR, W.DWORD, W.DWORD]
k32.CreateWaitableTimerExW.restype = _vp
k32.CreateWaitableTimerW.argtypes = [_vp, W.BOOL, W.LPCWSTR]
k32.CreateWaitableTimerW.restype = _vp
k32.SetWaitableTimer.argtypes = [
    _vp, ctypes.POINTER(ctypes.c_longlong), W.LONG, _vp, _vp, W.BOOL
]
k32.SetWaitableTimer.restype = W.BOOL
k32.CancelWaitableTimer.argtypes = [_vp]
k32.WaitForMultipleObjects.argtypes = [
    W.DWORD, ctypes.POINTER(_vp), W.BOOL, W.DWORD
]
k32.WaitForMultipleObjects.restype = W.DWORD


class NOTIFYICONDATAW(ctypes.Structure):
    _fields_ = [
        ("cbSize", W.DWORD), ("hWnd", _vp), ("uID", W.UINT),
        ("uFlags", W.UINT), ("uCallbackMessage", W.UINT),
        ("hIcon", _vp), ("szTip", W.WCHAR * 128),
        ("dwState", W.DWORD), ("dwStateMask", W.DWORD),
        ("szInfo", W.WCHAR * 256), ("uVersion", W.UINT),
        ("szInfoTitle", W.WCHAR * 64), ("dwInfoFlags", W.DWORD),
        ("guidItem", ctypes.c_byte * 16), ("hBalloonIcon", _vp)
    ]


WNDPROC = ctypes.WINFUNCTYPE(
    ctypes.c_ssize_t, _vp, W.UINT, W.WPARAM, W.LPARAM
)


class WNDCLASSW(ctypes.Structure):
    _fields_ = [
        ("style", W.UINT), ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int), ("cbWndExtra", ctypes.c_int),
        ("hInstance", _vp), ("hIcon", _vp), ("hCursor", _vp),
        ("hbrBackground", _vp), ("lpszMenuName", W.LPCWSTR),
        ("lpszClassName", W.LPCWSTR)
    ]


k32.GetModuleHandleW.argtypes = [W.LPCWSTR]
k32.GetModuleHandleW.restype = _vp
u32.DefWindowProcW.argtypes = [_vp, W.UINT, W.WPARAM, W.LPARAM]
u32.DefWindowProcW.restype = ctypes.c_ssize_t
u32.RegisterClassW.argtypes = [ctypes.POINTER(WNDCLASSW)]
u32.RegisterClassW.restype = W.ATOM
u32.CreateWindowExW.argtypes = [
    W.DWORD, W.LPCWSTR, W.LPCWSTR, W.DWORD,
    ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
    _vp, _vp, _vp, _vp
]
u32.CreateWindowExW.restype = _vp
u32.GetMessageW.argtypes = [ctypes.POINTER(W.MSG), _vp, W.UINT, W.UINT]
u32.GetMessageW.restype = ctypes.c_int
u32.TranslateMessage.argtypes = [ctypes.POINTER(W.MSG)]
u32.DispatchMessageW.argtypes = [ctypes.POINTER(W.MSG)]
u32.DispatchMessageW.restype = ctypes.c_ssize_t
u32.RegisterWindowMessageW.argtypes = [W.LPCWSTR]
u32.RegisterWindowMessageW.restype = W.UINT
u32.CreatePopupMenu.restype = _vp
u32.AppendMenuW.argtypes = [_vp, W.UINT, ctypes.c_size_t, W.LPCWSTR]
u32.TrackPopupMenu.argtypes = [
    _vp, W.UINT, ctypes.c_int, ctypes.c_int, ctypes.c_int, _vp, _vp
]
u32.TrackPopupMenu.restype = ctypes.c_int
u32.DestroyMenu.argtypes = [_vp]
u32.SetForegroundWindow.argtypes = [_vp]
u32.PostMessageW.argtypes = [_vp, W.UINT, W.WPARAM, W.LPARAM]
u32.GetCursorPos.argtypes = [ctypes.POINTER(W.POINT)]
u32.LoadImageW.argtypes = [
    _vp, W.LPCWSTR, W.UINT, ctypes.c_int, ctypes.c_int, W.UINT
]
u32.LoadImageW.restype = _vp
u32.LoadIconW.argtypes = [_vp, _vp]
u32.LoadIconW.restype = _vp
shl.Shell_NotifyIconW.argtypes = [W.DWORD, ctypes.POINTER(NOTIFYICONDATAW)]
shl.Shell_NotifyIconW.restype = W.BOOL

psapi = ctypes.WinDLL("psapi", use_last_error=True)
verdll = ctypes.WinDLL("version", use_last_error=True)

psapi.EnumProcessModulesEx.argtypes = [
    _vp, ctypes.POINTER(_vp), W.DWORD, ctypes.POINTER(W.DWORD), W.DWORD
]
psapi.EnumProcessModulesEx.restype = W.BOOL
psapi.GetModuleInformation.argtypes = [_vp, _vp, _vp, W.DWORD]
psapi.GetModuleInformation.restype = W.BOOL
k32.ReadProcessMemory.argtypes = [
    _vp, _vp, _vp, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)
]
k32.ReadProcessMemory.restype = W.BOOL
k32.VirtualQueryEx.argtypes = [_vp, _vp, _vp, ctypes.c_size_t]
k32.VirtualQueryEx.restype = ctypes.c_size_t
k32.GetExitCodeProcess.argtypes = [_vp, ctypes.POINTER(W.DWORD)]
k32.GetExitCodeProcess.restype = W.BOOL
verdll.GetFileVersionInfoSizeW.argtypes = [W.LPCWSTR, ctypes.POINTER(W.DWORD)]
verdll.GetFileVersionInfoSizeW.restype = W.DWORD
verdll.GetFileVersionInfoW.argtypes = [W.LPCWSTR, W.DWORD, W.DWORD, _vp]
verdll.GetFileVersionInfoW.restype = W.BOOL
verdll.VerQueryValueW.argtypes = [
    _vp, W.LPCWSTR, ctypes.POINTER(_vp), ctypes.POINTER(W.UINT)
]
verdll.VerQueryValueW.restype = W.BOOL


class MODULEINFO(ctypes.Structure):
    _fields_ = [
        ("lpBaseOfDll", _vp), ("SizeOfImage", W.DWORD), ("EntryPoint", _vp)
    ]


class MBI(ctypes.Structure):
    _fields_ = (
        [("BaseAddress", _vp), ("AllocationBase", _vp),
         ("AllocationProtect", W.DWORD)]
        + ([("PartitionId", W.WORD)] if ctypes.sizeof(_vp) == 8 else [])
        + [("RegionSize", ctypes.c_size_t), ("State", W.DWORD),
           ("Protect", W.DWORD), ("Type", W.DWORD)]
    )


class VSFFI(ctypes.Structure):
    _fields_ = [
        ("dwSignature", W.DWORD), ("dwStrucVersion", W.DWORD),
        ("dwFileVersionMS", W.DWORD), ("dwFileVersionLS", W.DWORD),
        ("dwProductVersionMS", W.DWORD), ("dwProductVersionLS", W.DWORD),
        ("dwFileFlagsMask", W.DWORD), ("dwFileFlags", W.DWORD),
        ("dwFileOS", W.DWORD), ("dwFileType", W.DWORD),
        ("dwFileSubtype", W.DWORD), ("dwFileDateMS", W.DWORD),
        ("dwFileDateLS", W.DWORD)
    ]


u32.GetClassNameW.argtypes = [_vp, W.LPWSTR, ctypes.c_int]
u32.GetClassNameW.restype = ctypes.c_int

u32.IsIconic.argtypes = [_vp]
u32.IsIconic.restype = W.BOOL
u32.ShowWindow.argtypes = [_vp, ctypes.c_int]
u32.ShowWindow.restype = W.BOOL
u32.AttachThreadInput.argtypes = [W.DWORD, W.DWORD, W.BOOL]
u32.AttachThreadInput.restype = W.BOOL
k32.GetCurrentThreadId.restype = W.DWORD


class _BIH(ctypes.Structure):
    _fields_ = [
        ("biSize", W.DWORD), ("biWidth", W.LONG),
        ("biHeight", W.LONG), ("biPlanes", W.WORD),
        ("biBitCount", W.WORD), ("biCompression", W.DWORD),
        ("biSizeImage", W.DWORD), ("biXPelsPerMeter", W.LONG),
        ("biYPelsPerMeter", W.LONG), ("biClrUsed", W.DWORD),
        ("biClrImportant", W.DWORD)
    ]


GWL_STYLE = -16
GWL_EXSTYLE = -20

WS_CAPTION = 0x00C00000
WS_THICKFRAME = 0x00040000
WS_SYSMENU = 0x00080000
WS_MINIMIZEBOX = 0x00020000
WS_MAXIMIZEBOX = 0x00010000
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_APPWINDOW = 0x00040000

SWP_FRAMECHANGED = 0x0020
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SW_MIN = 6

k32.CreateMutexW.argtypes = [_vp, W.BOOL, W.LPCWSTR]
k32.CreateMutexW.restype = _vp
u32.FindWindowW.argtypes = [W.LPCWSTR, W.LPCWSTR]
u32.FindWindowW.restype = _vp
u32.MessageBoxW.argtypes = [_vp, W.LPCWSTR, W.LPCWSTR, W.UINT]
u32.MessageBoxW.restype = ctypes.c_int
