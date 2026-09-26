"""
=============================================================================
AUTO-APPROVE BOT FOR IBM BOB 2.0 (VS CODE)
=============================================================================
Deskripsi:
Script otomatisasi mandiri untuk memantau layar laptop Anda, mengambil alih
dan otomatis meng-approve setiap perubahan/tool execution dari IBM BOB 2.0
sampai Bob menyelesaikan semua tugasnya dan memberikan kesimpulan akhir.

Fitur:
1. Native Windows GDI capture (ultra-cepat, DPI-aware, tanpa lag).
2. Deteksi akurat tombol "Approve once" / "Approve" (warna tema VS Code).
3. Deteksi status Bob (tombol merah Stop generation) vs status selesai.
4. Auto-exit dengan konfirmasi durasi saat Bob selesai memberikan kesimpulan.
5. Fail-safe darurat: Tekan [ESC], [Ctrl+C], atau gerakkan mouse ke pojok kiri atas (0, 0).
6. Nada notifikasi (audio chime) saat tombol di-approve dan saat selesai total.
=============================================================================
"""

import sys
import time
import os
import ctypes
from ctypes import windll, wintypes, byref
from PIL import Image

try:
    import winsound
    HAS_SOUND = True
except ImportError:
    HAS_SOUND = False

# Enable Per-Monitor DPI Awareness agar koordinat pixel 100% presisi
try:
    windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        windll.user32.SetProcessDPIAware()
    except Exception:
        pass

user32 = windll.user32
gdi32 = windll.gdi32

# Struktur untuk Bitmap capture GDI
class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ('biSize', wintypes.DWORD),
        ('biWidth', wintypes.LONG),
        ('biHeight', wintypes.LONG),
        ('biPlanes', wintypes.WORD),
        ('biBitCount', wintypes.WORD),
        ('biCompression', wintypes.DWORD),
        ('biSizeImage', wintypes.DWORD),
        ('biXPelsPerMeter', wintypes.LONG),
        ('biYPelsPerMeter', wintypes.LONG),
        ('biClrUsed', wintypes.DWORD),
        ('biClrImportant', wintypes.DWORD),
    ]

def get_screen_size():
    return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)

def capture_screen():
    w, h = get_screen_size()
    hScreenDC = user32.GetDC(0)
    hMemoryDC = gdi32.CreateCompatibleDC(hScreenDC)
    hBitmap = gdi32.CreateCompatibleBitmap(hScreenDC, w, h)
    gdi32.SelectObject(hMemoryDC, hBitmap)
    gdi32.BitBlt(hMemoryDC, 0, 0, w, h, hScreenDC, 0, 0, 0x00CC0020) # SRCCOPY

    bmi = BITMAPINFOHEADER()
    bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.biWidth = w
    bmi.biHeight = -h # top-down
    bmi.biPlanes = 1
    bmi.biBitCount = 32
    bmi.biCompression = 0

    buf = ctypes.create_string_buffer(w * h * 4)
    gdi32.GetDIBits(hMemoryDC, hBitmap, 0, h, buf, byref(bmi), 0)

    gdi32.DeleteObject(hBitmap)
    gdi32.DeleteDC(hMemoryDC)
    user32.ReleaseDC(0, hScreenDC)

    return Image.frombuffer('RGBA', (w, h), buf, 'raw', 'BGRA', 0, 1).convert('RGB')

def mouse_click(x, y):
    """Pindahkan kursor ke (x, y) dan klik kiri."""
    user32.SetCursorPos(int(x), int(y))
    time.sleep(0.04)
    user32.mouse_event(0x0002, 0, 0, 0, 0) # LEFTDOWN
    time.sleep(0.06)
    user32.mouse_event(0x0004, 0, 0, 0, 0) # LEFTUP

def get_mouse_pos():
    class POINT(ctypes.Structure):
        _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]
    pt = POINT()
    user32.GetCursorPos(byref(pt))
    return pt.x, pt.y

def is_esc_pressed():
    # VK_ESCAPE = 0x1B
    return bool(user32.GetAsyncKeyState(0x1B) & 0x8000)

def play_chime_approve():
    if HAS_SOUND:
        try:
            winsound.Beep(750, 80)
        except Exception:
            pass

def play_chime_done():
    if HAS_SOUND:
        try:
            winsound.Beep(523, 120)
            winsound.Beep(659, 120)
            winsound.Beep(784, 250)
            winsound.Beep(1046, 350)
        except Exception:
            pass

def find_approve_button(img):
    """
    Mencari tombol 'Approve once' / 'Approve' khas VS Code IBM BOB.
    Mendukung semua layout:
    - IBM Bob di sidebar kanan (Secondary Panel)
    - IBM Bob di Editor Tab tengah (Full width)
    - IBM Bob di sidebar kiri atau split view
    """
    img = img.convert('RGB')
    w, h = img.size
    pix = img.load()
    
    # Universal search: scan across the entire screen except activity bar & title/status bar
    # Activity bar is x < 0.05 * w, title bar is y < 0.14 * h, status bar is y > 0.92 * h
    x_min_search = int(w * 0.05)
    y_min_search = int(h * 0.15) # Melewati header pills (Pasted text, tokens, dll)
    y_max_search = int(h * 0.88)
    
    # Deteksi horizontal runs dengan warna cyan/blue button
    # Warna RGB VS Code primary button: R: 20-70, G: 85-165, B: 120-210
    runs = []
    step_y = 2
    step_x = 2
    
    for y in range(y_min_search, y_max_search, step_y):
        run_start = None
        for x in range(x_min_search, w - 10, step_x):
            r, g, b = pix[x, y][:3]
            is_cyan = (20 <= r <= 70 and 85 <= g <= 165 and 120 <= b <= 210)
            if is_cyan and run_start is None:
                run_start = x
            elif not is_cyan and run_start is not None:
                run_len = x - run_start
                # Tombol approve biasanya memiliki lebar signifikan
                if run_len >= int(w * 0.035): # ~35-70px tergantung resolusi
                    runs.append((y, run_start, x, run_len))
                run_start = None
        if run_start is not None:
            run_len = (w - 10) - run_start
            if run_len >= int(w * 0.035):
                runs.append((y, run_start, w - 10, run_len))

    if not runs:
        return None

    # Kelompokkan runs yang berdekatan vertikal untuk membentuk kotak tombol
    clusters = []
    current_cluster = [runs[0]]
    
    for r in runs[1:]:
        prev_y = current_cluster[-1][0]
        curr_y = r[0]
        if curr_y - prev_y <= step_y * 3:
            current_cluster.append(r)
        else:
            clusters.append(current_cluster)
            current_cluster = [r]
    if current_cluster:
        clusters.append(current_cluster)

    # Cari cluster terbaik yang menyerupai tombol
    for cluster in clusters:
        if len(cluster) >= 3: # minimal beberapa scan line
            c_ys = [c[0] for c in cluster]
            c_xs_start = [c[1] for c in cluster]
            c_xs_end = [c[2] for c in cluster]
            
            box_h = max(c_ys) - min(c_ys)
            box_w = max(c_xs_end) - min(c_xs_start)
            
            # Validasi proporsi tombol (lebar > tinggi, rasio w/h yang wajar)
            if 10 <= box_h <= 55 and box_w >= int(w * 0.035):
                center_x = (min(c_xs_start) + max(c_xs_end)) // 2
                center_y = (min(c_ys) + max(c_ys)) // 2
                return center_x, center_y, box_w, box_h

    return None

def is_bob_running(img):
    """
    Mengecek apakah Bob sedang aktif berpikir / running tool.
    Indikator utama: tombol merah 'Stop generation' (merah/coral)
    di pojok kanan bawah chat prompt box.
    """
    img = img.convert('RGB')
    w, h = img.size
    pix = img.load()
    
    # Cari di area prompt box pojok kanan bawah (x > 75%, y > 65%)
    x_start = int(w * 0.70)
    y_start = int(h * 0.65)
    
    red_count = 0
    step = 2
    for y in range(y_start, h - 30, step):
        for x in range(x_start, w - 10, step):
            r, g, b = pix[x, y][:3]
            # Warna merah/coral tombol stop VS Code (sekitar RGB 244, 135, 113 atau merah kuat)
            if r > 180 and g < 155 and b < 140 and (r - max(g, b) > 50):
                red_count += 1
                if red_count >= 5: # Cukup beberapa pixel merah kotak stop
                    return True
    return False

def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    w, h = get_screen_size()
    print("=" * 65)
    print(" 🤖 AUTO-APPROVE BOT UNTUK IBM BOB 2.0 (VS CODE)")
    print("=" * 65)
    print(f" Resolusi Layar   : {w} x {h}")
    print(f" Mode Operasi     : Continuous (Dapat dipakai berkali-kali)")
    print(f" Status Pengawas  : AKTIF & STANDBY")
    print(f" Fail-Safe        : Tekan [ESC] kapan saja atau mouse ke pojok (0,0)")
    print("-" * 65)
    print(" Bot akan mengawasi layar laptop dan otomatis meng-approve setiap")
    print(" aksi IBM Bob. Setelah Bob selesai memberikan kesimpulan, bot akan")
    print(" otomatis standby menunggu sesi Bob berikutnya tanpa perlu restart!")
    print("=" * 65)

    session_id = 1
    session_approvals = 0
    total_approvals = 0
    idle_streak_seconds = 0
    IDLE_TIMEOUT_TO_FINISH = 18 # detik konfirmasi setelah Bob idle & tanpa tombol
    had_activity = False
    in_session = False

    time.sleep(1.0)

    try:
        while True:
            # 1. Fail-Safe Checks
            if is_esc_pressed():
                print("\n\n[!] EMERGENCY STOP: Tombol ESC ditekan! Menghentikan bot...")
                break
            
            mx, my = get_mouse_pos()
            if mx <= 5 and my <= 5:
                print("\n\n[!] EMERGENCY STOP: Mouse digerakkan ke pojok kiri atas! Menghentikan bot...")
                break

            # 2. Tangkap layar saat ini
            screen = capture_screen()

            # 3. Cek tombol Approve dan status Bob
            btn = find_approve_button(screen)
            bob_active = is_bob_running(screen)

            if btn:
                if not in_session:
                    in_session = True
                    print(f"\n\n[{time.strftime('%H:%M:%S')}] 🚀 SESI #{session_id} DIMULAI: Tombol approval terdeteksi!")
                
                had_activity = True
                idle_streak_seconds = 0
                cx, cy, bw, bh = btn
                session_approvals += 1
                total_approvals += 1
                print(f"[{time.strftime('%H:%M:%S')}] ⚡ [Sesi #{session_id}] APPROVE #{session_approvals} di ({cx}, {cy}) -> Melakukan Klik...")
                mouse_click(cx, cy)
                play_chime_approve()
                time.sleep(1.0)
                continue

            # 4. Status aktivitas Bob
            if bob_active:
                if not in_session:
                    in_session = True
                    print(f"\n\n[{time.strftime('%H:%M:%S')}] 🚀 SESI #{session_id} DIMULAI: Bob terdeteksi aktif bekerja...")
                
                had_activity = True
                idle_streak_seconds = 0
                print(f"\r[{time.strftime('%H:%M:%S')}] ⏳ [Sesi #{session_id}] Bob sedang menjalankan perintah / berpikir... (Approvals: {session_approvals})", end="", flush=True)
                time.sleep(0.8)
            else:
                # Bob tidak aktif dan tidak ada tombol approve
                if had_activity or session_approvals > 0:
                    idle_streak_seconds += 1
                    sisa = max(0, IDLE_TIMEOUT_TO_FINISH - idle_streak_seconds)
                    print(f"\r[{time.strftime('%H:%M:%S')}] 🔍 [Sesi #{session_id}] Bob idle / menyusun kesimpulan... Memastikan selesai dalam {sisa}s ", end="", flush=True)
                    
                    if idle_streak_seconds >= IDLE_TIMEOUT_TO_FINISH:
                        print("\n\n" + "=" * 65)
                        print(f" 🎉 SESI #{session_id} SELESAI: IBM Bob 2.0 telah memberikan kesimpulan!")
                        print(f" 📊 Approval pada sesi ini : {session_approvals}")
                        print(f" 📈 Total kumulatif approval: {total_approvals}")
                        print(" 💤 Mode Standby: Bot siap otomatis untuk sesi Bob berikutnya!")
                        print("    (Tekan [ESC] atau [Ctrl+C] kapan saja jika ingin berhenti)")
                        print("=" * 65)
                        play_chime_done()
                        
                        # Reset untuk sesi berikutnya
                        session_id += 1
                        session_approvals = 0
                        idle_streak_seconds = 0
                        had_activity = False
                        in_session = False
                else:
                    print(f"\r[{time.strftime('%H:%M:%S')}] 👁️ [Standby] Menunggu aksi IBM BOB... (Sesi #{session_id} | Total Approved: {total_approvals})", end="", flush=True)
                
                time.sleep(1.0)

    except KeyboardInterrupt:
        print("\n\n[!] Bot dihentikan secara manual oleh pengguna (Ctrl+C).")
    except Exception as e:
        print(f"\n\n[X] Terjadi error: {e}")

    print(f"\n[✓] Program selesai. Total keseluruhan approval: {total_approvals}. Sampai jumpa!")

if __name__ == '__main__':
    main()
