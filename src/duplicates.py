import pandas as pd
from src.settings import DEFAULT_NODES_DIR
import numpy as np

nodes = pd.read_csv(DEFAULT_NODES_DIR, dtype=object)
names = nodes['label'].to_numpy(dtype=object)
ids = nodes['id'].to_numpy(dtype=np.int)
unique_names, unique_counts = np.unique(names, return_counts=True)
duplicate_counts = unique_counts[unique_counts > 1]
duplicate_names = unique_names[unique_counts > 1]
for name, count in list(zip(duplicate_names, duplicate_counts)):
    print(f"{name}: {count}")
pd.options.display.max_rows = 999
duplicate_nodes = nodes.loc[nodes['label'].isin(duplicate_names)]
sortedd = duplicate_nodes.sort_values(by='label')
print(sortedd)