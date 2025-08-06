import pandas as pd
import os

# Read the original dataset
df = pd.read_csv('../cardio_train.csv', sep=';')

# Shuffle the dataframe
df_shuffled = df.sample(frac=1, random_state=42).reset_index(drop=True)

# Calculate the size of each chunk
total_rows = len(df_shuffled)
chunk_size = total_rows // 3

# Split the dataframe into 3 parts
client1_df = df_shuffled[:chunk_size]
client2_df = df_shuffled[chunk_size:2*chunk_size]
client3_df = df_shuffled[2*chunk_size:]

# Save each part to a separate CSV file
client1_df.to_csv('client1_data.csv', index=False)
client2_df.to_csv('client2_data.csv', index=False)
client3_df.to_csv('client3_data.csv', index=False)

print(f"Dataset split into 3 files:")
print(f"  client1_data.csv: {len(client1_df)} rows")
print(f"  client2_data.csv: {len(client2_df)} rows")
print(f"  client3_data.csv: {len(client3_df)} rows")