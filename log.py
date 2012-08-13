# $Id: log.py 171387 2011-06-20 06:45:14Z krasznaa $
#
# Basic logging functionality for the Python scripts.
#

##
# @short Create a standard logger
#
# This function can be used to create a standard logger object
# for the python scripts.
#
# @param name The name of the log source
# @returns A logging.Logger object
def getLogger( name ):
    # Set the format of the log messages:
    FORMAT = 'Py:%(name)-25s  %(levelname)-8s  %(message)s'
    import logging
    logging.basicConfig( format = FORMAT )
    # Create the logger object:
    logger = logging.getLogger( name )
    # Set the following to DEBUG when debugging the scripts:
    logger.setLevel( logging.INFO )
    return logger
