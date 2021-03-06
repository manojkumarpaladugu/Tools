import os
import sys

# Traverse all directories recursively and delete all the files except .efi and .pdb
for root, dirs, files in os.walk(sys.argv[1]):
    for file in files:
        full_path = os.path.join(root, file)
        if (not full_path.endswith('.efi')) and (not full_path.endswith('.pdb')):
            try:
                os.remove(full_path)
            except FileNotFoundError:
                # We hit this exception due to longer file path. So skipping
                pass
