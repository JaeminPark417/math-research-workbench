"""Small filesystem adapter for cooperating local ticket clients.

POSIX uses directory descriptors and no-follow opens. Windows uses checked
absolute paths, rejects reparse points, and locks byte zero with msvcrt. These
checks do not sandbox hostile concurrent filesystem writers. Windows stdlib
cannot fsync directories; recovery is for process interruption, not a promise
of durability against power loss. Keep stores on a local filesystem.
"""
import errno
import os
from pathlib import Path
import stat

WINDOWS = os.name == 'nt'


def is_link(info):
    return stat.S_ISLNK(info.st_mode) or bool(
        getattr(info, 'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400))


def checked_path(value, missing=False):
    path = Path(value).absolute()
    for item in (*reversed(path.parents), path):
        try:
            info = item.lstat()
        except FileNotFoundError:
            if missing and item == path:
                break
            raise
        if is_link(info):
            raise OSError(errno.ELOOP, 'Links and reparse points are not allowed.')
    return path


def open_dir(path, parent=None):
    if WINDOWS:
        result = checked_path(Path(parent) / path if parent is not None else path)
        if not result.is_dir():
            raise NotADirectoryError(result)
        return result
    return os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)


def open_file(path, flags, mode=0o600, parent=None):
    if WINDOWS:
        target = checked_path(Path(parent) / path if parent is not None else path,
                              missing=bool(flags & os.O_CREAT))
        fd = os.open(target, flags | os.O_BINARY, mode)
        try:
            checked_path(target)
            if not os.path.samestat(target.stat(), os.fstat(fd)):
                raise OSError(errno.EAGAIN, 'File changed while opening.')
        except BaseException:
            os.close(fd)
            raise
        return fd
    return os.open(path, flags | os.O_NOFOLLOW | os.O_NONBLOCK, mode, dir_fd=parent)


def try_lock(fd):
    if WINDOWS:
        import msvcrt
        os.lseek(fd, 0, os.SEEK_SET)
        try:
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        except OSError as error:
            if error.errno in (errno.EACCES, errno.EAGAIN, errno.EDEADLK):
                raise BlockingIOError(error.errno, 'Another process holds the lock.') from error
            raise
    else:
        import fcntl
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)


def sync_dir(directory):
    if WINDOWS:
        checked_path(directory)
    else:
        os.fsync(directory)


def close_dir(directory):
    if not WINDOWS:
        os.close(directory)


def replace(source, target, directory):
    if WINDOWS:
        source = checked_path(Path(directory) / source)
        target = checked_path(Path(directory) / target, missing=True)
        os.replace(source, target)
    else:
        os.replace(source, target, src_dir_fd=directory, dst_dir_fd=directory)


def link(source, target, directory):
    if WINDOWS:
        source = checked_path(Path(directory) / source)
        target = checked_path(Path(directory) / target, missing=True)
        os.link(source, target)  # Fails if target exists; no overwrite.
    else:
        os.link(source, target, src_dir_fd=directory, dst_dir_fd=directory, follow_symlinks=False)


def unlink(name, directory):
    if WINDOWS:
        os.unlink(checked_path(Path(directory) / name))
    else:
        os.unlink(name, dir_fd=directory)
