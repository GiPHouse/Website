import os

###################################################################################################
# This module maintains constants to print in specific colours.                                   #
###################################################################################################

RED = "\033[1;31m"
GREEN = "\033[1;32m"
YELLOW = "\033[1;33m"
BROWN = "\033[33m"
CYAN = "\033[36m"
PURPLE = "\033[35m"
BRED = "\033[41m"
DARKGREEN = "\033[32m"
RESET = "\033[0m"


# call this at the start of the process to ensure that colours are printed properly
def initialise_colours():
    os.system("")
