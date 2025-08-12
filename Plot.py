# Add labels showing both x and y values
for i in range(len(x)):
    ax.annotate(f'({x[i]}, {y[i]})', 
                (x[i], y[i]), 
                textcoords="offset points", 
                xytext=(5, 5),
                fontsize=10, 
                color='blue',
                ha='left')  # horizontal alignment

plt.show()
