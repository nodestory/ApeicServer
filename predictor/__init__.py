import sys
import os
real_path = os.path.realpath(__file__)
dir_name = os.path.dirname(real_path)
root_dir_name = os.path.dirname(dir_name)
# sys.path.append(dir_name)
sys.path.append('%s/apeic/' % root_dir_name)
print '%s/apeic/' % root_dir_name
# sys.path.append('%s/predictor/' % dir_name)

# import sys
sys.path.append('/home/linzy/Projects/ApeicServer/apeic')
sys.path.append('/home/linzy/Projects/ApeicServer/predictor')


import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir) 

import apeic
from apeic.apeic_db_manager import *