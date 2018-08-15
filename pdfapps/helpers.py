import sys
import shutil

perm_err = 'ERROR: You do not have permission to write to {}. Close any application that might be accessing that ' \
           'file and/or try running this program again as a superuser/administrator.'

def oats_copy(src, dst):
    try:
        shutil.copy(src, dst)
    except PermissionError:
        sys.exit(perm_err.format(dst))


def oats_move(src, dst):
    try:
        shutil.move(src, dst)
    except PermissionError:
        sys.exit(perm_err.format(dst))

