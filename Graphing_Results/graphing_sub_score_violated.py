import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

#For the 

df = pd.read_csv('Best Practices Metrics - Final.csv')

# filter data by categories 2, 3, and 10:
categories_to_plot = [2, 3, 10]
for category in categories_to_plot:
    # Filter data for the current category - split it by the category here
    category_data = df[df['identified category'].notna() & df['identified category'].astype(str).str.contains(f'\\b{category}\\b')]

    # flatten column 'violated subcategories' 
    flattened_list = []
    for sublist in category_data['violated subcategories'].dropna(): #just in case we run into any na values
        for item in str(sublist).split(','): #delimiter is ,
            try:
                flattened_list.append(float(item))
            #some of the values were not a consistent format --> skipping
            except ValueError:
                print(f"Skipping invalid value: {item}")

    # count occurrences of each subcategory using Series
    category_counts = pd.Series(flattened_list).value_counts().sort_index()

    # Create evenly spaced x positions for the bars
    x_positions = np.arange(len(category_counts))

    # Plot the bar graph for the current category
    plt.figure(figsize=(10, 6))
    plt.bar(x_positions, category_counts.values, color='#b0c4de', width=0.6)
    plt.title(f'Violated Best Practices - Subcategories (Category {category})')
    plt.xlabel('Violated Subcategories')
    plt.ylabel('Count')
    plt.xticks(x_positions, [str(subcat) for subcat in category_counts.index], rotation=45, ha='right')
    plt.tight_layout()
    plt.show()
