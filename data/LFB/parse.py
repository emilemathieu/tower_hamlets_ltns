#%%
import os


f = open("all.csv", "r")
data = f.read()
# print(data)

# Split the data into lines
lines = data.split('\n')

# Select every third line
selected_lines = [line for i, line in enumerate(lines) if (i + 2) % 3 == 0]

# Print the selected lines
for line in selected_lines:
    print(line)
# %%
