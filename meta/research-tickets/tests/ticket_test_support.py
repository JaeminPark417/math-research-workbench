"""Narrow test-only handling for Windows symlink privileges."""
import os

def symlink_or_skip(case, link, target, target_is_directory=False):
    try:
        link.symlink_to(target, target_is_directory=target_is_directory)
    except OSError as error:
        if os.name == 'nt' and getattr(error, 'winerror', None) == 1314:
            case.skipTest('This symlink case requires Windows Developer Mode or symlink privilege.')
        raise
