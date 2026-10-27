
import pandas as pd

file_path = "test-00000-of-00001.parquet"

df = pd.read_parquet(file_path)

print("Dataset shape:", df.shape)
print("\nColumn names:")
print(df.columns.tolist())

print("\nFirst 10 records:")
print(df.head(10).to_string(index=False))
