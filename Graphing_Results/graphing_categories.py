import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('Best Practices Metrics - Final.csv')

#flatten category column because there could be multiple idenitfied categories in one cell
flattened_list = [int(item) for sublist in df['identified category'].dropna() for item in str(sublist).split(',')]
#get count for each category using Series
category_counts = pd.Series(flattened_list).value_counts()


# sort the categories by count in descending order #1-#12
sorted_categories = category_counts.sort_values(ascending=False)

# display sorted categories in bar graph
plt.bar(sorted_categories.index, sorted_categories.values, color='#1f77b4')
plt.xlabel('Codebook Categories')
plt.ylabel('Count')
plt.title('Occurance of Codebook Categories')


plt.show()