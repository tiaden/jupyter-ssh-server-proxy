import os
import shutil
import subprocess

from typing import Any, Dict

HOSTKEY_PATH = os.path.expanduser('~/.ssh/jupyter_sshd_hostkey')
AUTHORIZED_KEYS_PATH = os.environ.get('JUPYTER_SSHD_PROXY_AUTHORIZED_KEYS_PATH', '.ssh/authorized_keys .ssh/authorized_keys2')
SSHD_LOG_LEVEL = os.environ.get('JUPYTER_SSHD_PROXY_LOG_LEVEL', 'INFO')
USE_FALL_BACK = os.environ.get('JUPYTER_SSHD_USE_FALL_BACK', False)

def setup_sshd() -> Dict[str, Any]:
    cmd =[]
    if not USE_FALL_BACK:
        sshd_path = shutil.which('mchub')
        if sshd_path:
            cmd = [
                sshd_path, 'ssh-server', '-l', '127.0.0.1:{port}',
            ]
    else:
        if not os.path.exists(HOSTKEY_PATH):
            # Create a per-user hostkey if it does not exist
            os.makedirs(os.path.dirname(HOSTKEY_PATH), mode=0o700, exist_ok=True)
            subprocess.check_call(['ssh-keygen', '-f', HOSTKEY_PATH, '-q', '-N', ''])

        sshd_path = shutil.which('sshd')

        if sshd_path:
            cmd = [
                sshd_path, '-h', HOSTKEY_PATH, '-D', '-e',
                # Intentionally have sshd ignore global config
                '-f', 'none',
                '-o', 'ListenAddress 127.0.0.1:{port}',
                # Last login info is from /var/log/lastlog, which is transient in containerized systems
                '-o', 'PrintLastLog no',
                '-o', f'AuthorizedKeysFile {AUTHORIZED_KEYS_PATH}',
                '-o', f'LogLevel {SSHD_LOG_LEVEL}',
                # Default to enabling sftp
                '-o', 'Subsystem    sftp    internal-sftp'
            ]
    if not cmd:
        return {}

    return {
        "command": cmd,
        "raw_socket_proxy": True,
        "timeout": 60,
        "launcher_entry": {"enabled": False},
    }
