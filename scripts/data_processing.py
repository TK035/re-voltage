import pandas as pd

def preprocess_data(input_path, output_path):
    df = pd.read_csv(input_path)
    df = df[df['distance_to_station'] <= 5]
    df.to_csv(output_path, index = False)
    return df