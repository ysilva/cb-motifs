from pathlib import Path

import numpy as np
from matplotlib import pyplot as plt
import database


deltas = database.query_comment_log_time_deltas()
data = np.array(deltas)
percentile_95 = np.percentile(data, 95)
print(percentile_95)
image_name = Path("time_deltas.png")
data = np.array(deltas)
_, ax = plt.subplots()
ax.hist(data, bins=100)
ax.axvline(percentile_95, color="black")
plt.savefig(image_name, dpi=100, bbox_inches="tight")
