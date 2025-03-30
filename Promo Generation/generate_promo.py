import subprocess

image_path = "inputs/final1.jpeg"
audio_path = "inputs/audio_sample.mp3"
output_dir = "results"

cmd = [
    "python3", "inference.py",
    "--driven_audio", audio_path,
    "--source_image", image_path,
    "--result_dir", output_dir,
    "--still",  # Keeps head still
    "--preprocess", "full"  # options: crop, full, extcrop, extfull
]

subprocess.run(cmd)
