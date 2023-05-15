import os
import json
import logging
import sys
from colorlog import ColoredFormatter

# Define a custom formatter with colors
formatter = ColoredFormatter(
    "%(log_color)s%(levelname)-8s%(reset)s %(blue)s%(message)s",
    datefmt=None,
    reset=True,
    log_colors={
        'DEBUG':    'cyan',
        'INFO':     'green',
        'WARNING':  'yellow',
        'ERROR':    'red',
        'CRITICAL': 'red,bg_white',
    },
    secondary_log_colors={},
    style='%'
)

# Create a StreamHandler with the custom formatter
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(formatter)

# Set the root logger to use the custom handler
logging.root.setLevel(logging.DEBUG)
logging.root.addHandler(handler)

if __name__ == "__main__":
    logging.info('Setting environment')
    os.environ['ALL_SOURCES'] = '1'
    os.environ['NO_MAGIC'] = '1'

    logging.info('Creating xcframework for iOS and macOS platforms')
    cmd = (
		'set -o pipefail && '
		'swift create-xcframework '
		'--platform iOS '
		'--platform macOS '
		'--xcconfig config.xcconfig '
		'| xcpretty'
	)
    result = os.system(cmd)
    if result != 0:
        logging.error('Failed to create xcframework')
        sys.exit(1)

    if not os.path.exists('binaries'):
        logging.info('Creating binaries directory')
        os.system('mkdir binaries')

    data = json.loads(os.popen(f'swift package dump-package').read())
    targets_data = data.get('targets', [])
    for target in targets_data:
        if not target.get('type', '') == 'regular': continue
        name = target.get('name', '')
        logging.info(f'Creating directory for {name} target')
        target_sha = os.popen(f'git log --pretty=format:\'%H\' -1 -- {name}').read()
        os.system(f'mkdir -p binaries/{target_sha}')
        logging.info(f'Moving {name}.xcframework to binaries/{target_sha}')
        os.system(f'mv {name}.xcframework binaries/{target_sha}/{name}.xcframework')
    logging.info('Finished updating cache')