import sys
import os
real_path = os.path.realpath(__file__)
dir_name = os.path.dirname(real_path)
sys.path.append(dir_name)
print dir_name

sys.path.append('/home/linzy/Projects/ApeicServer/predictor')