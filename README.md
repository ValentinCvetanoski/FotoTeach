# FotoTeach
FotoTeach is a powerful Python desktop application for advanced photo analysis. It evaluates technical quality, composition, and metadata, providing actionable feedback for photographers to improve their images.

✨ Features
🖼️ Supports JPG, PNG, TIFF + RAW formats (DNG, ARW, NEF, CR2)
📊 Technical Analysis – exposure, brightness, motion blur detection
🎚️ Contrast & Dynamic Range Evaluation
🔊 Noise Detection & Recommendations
🙂 Face Detection + Focus Scoring
📐 Leading Lines Detection (composition)
✂️ Smart Crop Suggestions (rule of thirds, subject-based, etc.)
📷 Metadata Extraction (camera, focal length, aperture via ExifTool)
👁️ Visual overlays for real-time analysis

🛠️ Tech Stack
Python
OpenCV (cv2)
NumPy
Tkinter (GUI)
Pillow (image display)
rawpy (RAW image support)
ExifTool (metadata extraction)

⚙️ How It Works
Load an image (including RAW formats)
App processes image using computer vision techniques
Detects faces, edges, contrast, noise, and composition patterns
Extracts metadata (if ExifTool is installed)
Displays a full analysis report + visual overlays

🚀 Getting Started
1. Install dependencies
pip install opencv-python numpy pillow rawpy

3. Install ExifTool

Download from: https://exiftool.org/

Make sure it's added to your system PATH.

3. Run the app
python app.py

📁 Project Structure
project/
  ├── photo_analyzer.py
  ├── deploy.prototxt
  ├── res10_300x300_ssd_iter_140000.caffemodel
  ├── photo_analysis.log

📊 Analysis Breakdown
Technical: Exposure, blur (Laplacian variance), brightness
Contrast: Histogram-based dynamic range
Noise: Estimated via denoising comparison
Faces: Detection + sharpness scoring
Composition:
Leading lines (Hough Transform)
Subject detection (saliency + edges + faces)
Crop suggestions

⚠️ Notes
ExifTool is required for metadata extraction
Large RAW files may take longer to process
Face detection requires included model files

💡 Future Improvements
🎨 AI-based aesthetic scoring
📷 Lightroom preset suggestions
⚡ GPU acceleration
🌙 Modern UI redesign

📌 Use Cases
Photographers analyzing shot quality
Learning composition techniques
Post-processing decision support

📄 License
GNU v3
