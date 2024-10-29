from kaseki.bruteforce import *
from typing import Union, Type
import queue as q
import multiprocessing as mp

from kaseki.bruteforce.protocol import Protocol, SSH, FTP
from kaseki.bruteforce.login import Login, SSHLogin, FTPLogin
from kaseki.bruteforce.target import Target, SSHTarget, FTPTarget

    
def get_login_type_with_target(target: Target) -> Type[Login]:
    if isinstance(target, SSHTarget):
        return SSHLogin
    elif isinstance(target, FTPTarget):
        return FTPLogin
    return Login

def get_login_type_with_protocol(protocol: Protocol) -> Type[Login]:
    if isinstance(protocol, SSH):
        return SSHLogin
    elif isinstance(protocol, FTP):
        return FTPLogin
    return Login


__all__ = ['get_login_type_with_target', 'get_login_type_with_protocol']