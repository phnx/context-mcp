import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# ------------------------------------------------------------
# Load Data
# ------------------------------------------------------------

base = Path("test/prompt_test/test_result")

variants = [f"variant_{i}" for i in range(1, 6)]

tools = {}
hit_miss = {}

for v in variants:
    tool_file = base / f"{v}_tool.json"
    result_file = base / f"{v}_result.json"

    with tool_file.open() as f:
        tool_data = json.load(f)

    with result_file.open() as f:
        result_data = json.load(f)

    hit_miss[v] = result_data

    for tool_name, metrics in tool_data.items():
        if tool_name not in tools:
            tools[tool_name] = {}
        tools[tool_name][v] = metrics


# ------------------------------------------------------------
# Plotting
# ------------------------------------------------------------

metrics = ["calls", "tokens_in", "tokens_out"]
tool_names = list(tools.keys())
x = np.arange(len(variants))

fig, axes = plt.subplots(4, 1, figsize=(14, 20))

# Increase vertical spacing between rows
plt.subplots_adjust(hspace=1)

bar_containers = []

# ------------------------------
# 1–3: Tool usage metrics
# ------------------------------

for ax, metric in zip(axes[:3], metrics):

    width = 0.8 / len(tool_names)

    for idx, tool_name in enumerate(tool_names):
        values = [tools[tool_name].get(v, {}).get(metric, 0) for v in variants]

        bars = ax.bar(
            x + idx * width,
            values,
            width,
            label=tool_name,
        )

        if ax is axes[0]:
            bar_containers.append(bars)

    # ax.set_title(metric, fontsize=14)
    ax.set_xticks(x + width * len(tool_names) / 2)
    ax.set_xticklabels(variants)
    ax.set_ylabel(metric)


# ------------------------------
# 4: Hit/Miss Plot
# ------------------------------

ax = axes[3]

hit_values = [hit_miss[v]["hit"] for v in variants]
miss_values = [hit_miss[v]["miss"] for v in variants]

width = 0.35

hit_bars = ax.bar(x - width / 2, hit_values, width, label="Hit")
miss_bars = ax.bar(x + width / 2, miss_values, width, label="Miss")

# ax.set_title("Hit/Miss Summary", fontsize=14)
ax.set_xticks(x)
ax.set_xticklabels(variants)
ax.set_ylabel("Count")

# Legend (only for hit/miss, small)
ax.legend()


# ------------------------------------------------------------
# Shared legend (for tool usage only)
# ------------------------------------------------------------

fig.legend(
    [bc[0] for bc in bar_containers],
    tool_names,
    loc="lower center",
    ncol=6,  # <<< 6 columns legend
    bbox_to_anchor=(0.5, 0.01),
)

plt.tight_layout(rect=[0, 0.07, 1, 1])
plt.show()


# ------------------------------------------------------------
# Print hit/miss summary
# ------------------------------------------------------------

print("\n=== Hit/Miss Summary ===")
for v in variants:
    print(f"{v}: hits={hit_miss[v]['hit']}, miss={hit_miss[v]['miss']}")
