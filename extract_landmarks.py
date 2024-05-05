from landmark_class import CreateDataLandmarks

landmarks_file = "./data/landmark_names.inp"
save_dir = "./data"
from_csv = "./data/data.csv"
CreateDataLandmarks(landmarks_file, save_dir, from_csv)
