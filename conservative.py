# Create figure and primary axis
fig, ax1 = plt.subplots(figsize=(10, 6))

# Plot first line on primary y-axis
color = 'tab:blue'
ax1.set_xlabel('Time')
ax1.set_ylabel('First Variable', color=color)
line1 = ax1.plot(x, y1, color=color, label='Sine Wave', linewidth=2)
ax1.tick_params(axis='y', labelcolor=color)
ax1.grid(True, alpha=0.3)

# Create secondary y-axis and plot second line
ax2 = ax1.twinx()
color = 'tab:red'
ax2.set_ylabel('Second Variable', color=color)
line2 = ax2.plot(x, y2, color=color, label='Exponential', linewidth=2, linestyle='--')
ax2.tick_params(axis='y', labelcolor=color)

# Add legend for both lines
lines = line1 + line2
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc='upper left')

plt.title('Two Lines with Different Y-Axes')
plt.tight_layout()
plt.show()
