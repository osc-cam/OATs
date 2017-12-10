import sys
import shutil

def oats_copy(src, dst):
    try:
        shutil.copy(src, dst)
    except PermissionError:
        sys.exit('\nERROR: You do not have permission to write to ' + dst +
                '\nPlease run OASIS again as a superuser/administrator.')


def oats_move(src, dst):
    try:
        shutil.move(src, dst)
    except PermissionError:
        sys.exit('\nERROR: You do not have permission to write to ' + dst +
                '\nPlease run OASIS again as a superuser/administrator.')

