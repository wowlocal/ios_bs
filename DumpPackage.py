import json
import os

class Target:
    def __init__(self, path: str, binary: bool):
        self.path = path
        self.binary = binary

    def __repr__(self):
        return f'Target(path={self.path}, binary={self.binary})'


def parse_swift_dump_package(s: str) -> list[Target]:
    data = json.loads(s)
    targets_data = data.get('targets', [])
    targets = []
    for target_data in targets_data:
        path = target_data.get('path', '')
        binary = target_data.get('type', '') == 'binary'
        targets.append(Target(path, binary))
    return targets

# parse swift package dump-package output
dump_package_output = os.popen('swift package dump-package').read()
targets = parse_swift_dump_package(dump_package_output)
for target in targets:
    print(target)
