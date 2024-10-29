from kaseki.bruteforce.target import Target, SSHTarget, FTPTarget
from kaseki.bruteforce.protocol import SSH, FTP, Protocol
from kaseki.bruteforce.login import Login, SSHLogin, FTPLogin

from typing import Type


def get_protocol_type_with_login(login_obj: Login) -> Type[Protocol]:
    if isinstance(login_obj, SSHLogin):
        return SSH
    elif isinstance(login_obj, FTPLogin):
        return FTP
    return Protocol

def get_protocol_type_with_target(target_obj: Target) -> Type[Protocol]:
    if isinstance(target_obj, SSHTarget):
        return SSH
    elif isinstance(target_obj, FTPTarget):
        return FTP
    return Protocol

__all__ = [
    'get_protocol_type_with_login',
    'get_protocol_type_with_target'
]