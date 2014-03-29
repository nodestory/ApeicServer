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