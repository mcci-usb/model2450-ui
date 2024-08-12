
##############################################################################
# 
# Module: main.py
#
# Description:
#     Main program entry point.
#
# Author:
#     Vinay N, MCCI Corporation Aug 2024
#
# Revision history:
#     V1.0.0 Mon Aug 12 2024 01:00:00   Vinay N 
#       Module created

##############################################################################
# Built-in imports
import os

# Own modules
import uiMainApp

__author__ = 'Vinay N'
__contact__ = 'vinayn@mcci.com'
__maintainer__ = ['Vinay N']
__status__ = 'Production'
__version__ = '1.0.0'
##############################################################################
# Utilities
##############################################################################
def main ():
    """
    Main program entry point
    Args:
        No argument
    Return:
        None
    """
    # Determine the base directory path
    base = os.path.abspath(os.path.dirname(__file__))

    # If this file is within an archive, get its parent directory
    if not os.path.isdir(base):
        base = os.path.dirname(base)

    # Since this file lives in lib/, get the parent directory
    base = os.path.dirname(base)

    # Run the application
    uiMainApp.run()

# python program to use
# main for function call.
if __name__ == '__main__':
    main()