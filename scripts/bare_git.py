import socket
import select
import os
import json

"""
mkdir empty-repo
cd empty-repo
git init
swift package init
git add .
git commit -m "empty lib"
# запускаем git сервер
git daemon --reuseaddr --base-path=. --export-all --verbose --enable=receive-pack
# запускаем прокси
python3 bare_git.py
"""

GIT_DAEMON_PORT = 9418
PROXY_PORT = 12345
BUFFER_SIZE = 4096

class Target:
    def __init__(self, name: str, path: str, binary: bool, buildable: bool):
        self.name = name
        self.path = path
        self.binary = binary
        self.buildable = buildable

    def __repr__(self):
        return f'Target(name={self.name}, path={self.path}, binary={self.binary})'


def parse_swift_dump_package(s: str) -> list[Target]:
    data = json.loads(s)
    targets_data = data.get('targets', [])
    targets = []
    for target_data in targets_data:
        name = target_data.get('name', '')
        path = target_data.get('path', '')
        binary = target_data.get('type', '') == 'binary'
        buildable = target_data.get('type', '') == 'regular'
        targets.append(Target(name, path, binary, buildable))
    return targets

def make(path_string):
    dump_package_output = os.popen(f'cd {path_string} && swift package dump-package').read()
    targets = parse_swift_dump_package(dump_package_output)

    for target in targets:
        if target.binary:
            target_sha = os.popen(f'cd {path_string} && git log --pretty=format:\'%H\' -1 -- {target.name}').read()
            print('copying binary ' + os.path.join('binaries', target_sha, f'{target.name}.xcframework') + ' to ' + os.path.join(path_string, target.name))
            # check if file exists
            path_to_xcframework = os.path.join(path_string, 'binaries', target_sha, f'{target.name}.xcframework')
            if not os.path.exists(path_to_xcframework):
                os.system(f'cd {path_string} && python3 update_cache.py')
            # cp xcframeworks from binaries/ to dirs in path_string
            os.system('cp -Rf ' + path_to_xcframework + ' ' + os.path.join(path_string, target.name))
        else:
            if not target.buildable: continue
            xcframework_path = os.path.join(path_string, target.name, f'{target.name}.xcframework')
            print('removing ' + xcframework_path)
            if os.path.exists(xcframework_path):
                os.system('rm -rf ' + f'"{xcframework_path}"')

def remove_dirs_starting_with(path_string, prefix, exception):
    for f in os.listdir(path_string):
        if f.startswith(prefix) and not f.startswith(exception):
            os.system("rm -rf " + os.path.join(path_string, f))

def forward_data(src, dst):
    data = src.recv(BUFFER_SIZE)
    if len(data) == 0:
        return False

    if b"git-upload-pack" in data:
		# Extract the repository path
        repo_path = data.split(b"git-upload-pack")[1].split(b"\0")[0].decode().strip()
        make(os.path.dirname(repo_path))
        caches_path = os.path.join(os.path.expanduser("~"), "Library/Caches/org.swift.swiftpm/repositories/")
        remove_dirs_starting_with(caches_path,
                                  "__dummy__",
                                  os.path.basename(repo_path))
        dst.sendall(b'0036git-upload-pack /\x00host=localhost:12345\x00\x00version=2\x00')
    else:
        dst.sendall(data)
    return True

def main():
    git_daemon = ('localhost', GIT_DAEMON_PORT)
    proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    proxy_socket.bind(('0.0.0.0', PROXY_PORT))
    proxy_socket.listen(10)

    print(f"Proxy listening on port {PROXY_PORT}...")

    while True:
        client_socket, client_address = proxy_socket.accept()
        print(f"Connection from {client_address}")

        git_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        git_socket.connect(git_daemon)

        while True:
            rlist, _, _ = select.select([client_socket, git_socket], [], [])
            if client_socket in rlist:
                if not forward_data(client_socket, git_socket):
                    break
            if git_socket in rlist:
                if not forward_data(git_socket, client_socket):
                    break

        client_socket.close()
        git_socket.close()

if __name__ == "__main__":
    main()
