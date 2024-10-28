from .target import Target
from .target_ssh import SSHTarget
from .target_ftp import FTPTarget

from . import target
from . import target_ssh
from . import target_ftp

__all__ = [
    *target.__all__,
    *target_ssh.__all__,
    *target_ftp.__all__
]