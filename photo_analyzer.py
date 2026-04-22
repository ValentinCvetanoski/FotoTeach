import cv2
import numpy as np
import logging
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import os
import time
import rawpy
import exiftool
import subprocess

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('photo_analysis.log'),
        logging.StreamHandler()
    ]
)

class PhotoAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Professional Photo Analyzer")
        self.root.geometry("1400x900")
        self.original_image = None
        self.display_image = None
        self.analysis = {}
        self.current_image_path = ""
        self.exif_tool_installed = self._check_exif_tool_installed()
        self.create_widgets()

    def _check_exif_tool_installed(self):
        """Check if ExifTool is installed and accessible."""
        try:
            result = subprocess.run(['exiftool', '-ver'], capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False

    def create_widgets(self):
        # Left panel - Image display
        self.image_frame = ttk.Frame(self.root, width=1000, height=800)
        self.image_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(self.image_frame, bg='#2d2d2d')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Right panel - Controls and analysis
        control_frame = ttk.Frame(self.root, width=400)
        control_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=10, pady=10)
        
        # File selection
        ttk.Button(control_frame, text="Open Image", command=self.load_image).pack(pady=5)
        ttk.Button(control_frame, text="Analyze Composition", command=self.run_analysis).pack(pady=5)
        
        # Results display
        self.results_text = tk.Text(control_frame, height=35, width=55, bg='#1e1e1e', fg='white')
        self.results_text.pack(pady=10)
        
        # Progress bar
        self.progress = ttk.Progressbar(control_frame, orient=tk.HORIZONTAL, mode='determinate')
        self.progress.pack(fill=tk.X)
    
    def load_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.jpg *.jpeg *.png *.tiff *.tif *.dng *.arw *.nef *.cr2")]
        )
        if file_path:
            self.current_image_path = file_path
            self.original_image = self._load_image_file(file_path)
            if self.original_image is not None:
                self.show_image()
    
    def _load_image_file(self, file_path):
        """Load image including RAW formats"""
        try:
            if file_path.lower().endswith(('.dng', '.arw', '.nef', '.cr2')):
                with rawpy.imread(file_path) as raw:
                    rgb = raw.postprocess()
                return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
            else:
                return cv2.imread(file_path)
        except Exception as e:
            logging.error(f"Error loading image: {str(e)}")
            return None

    def show_image(self, analysis_overlay=None):
        if self.original_image is None:
            return
        
        display_image = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2RGB).copy()
        
        # Apply analysis overlays
        if analysis_overlay:
            if 'crops' in analysis_overlay:
                for crop in analysis_overlay['crops']:
                    x1, y1, x2, y2 = crop
                    cv2.rectangle(display_image, (x1, y1), (x2, y2), (0,255,0), 3)
            
            if 'faces' in analysis_overlay:
                for (x, y, w, h), focused in analysis_overlay['faces']:
                    color = (0, 255, 0) if focused else (0, 0, 255)
                    cv2.rectangle(display_image, (x, y), (x+w, y+h), color, 2)
            
            if 'lines' in analysis_overlay:
                for line in analysis_overlay['lines']:
                    x1, y1, x2, y2 = line
                    cv2.line(display_image, (x1, y1), (x2, y2), (255,0,0), 2)
        
        # Resize for display
        img = Image.fromarray(display_image)
        img.thumbnail((1000, 800), Image.LANCZOS)
        self.display_image = ImageTk.PhotoImage(img)
        
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.display_image)
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))
        self.root.update()
    
    def run_analysis(self):
        if self.original_image is None:
            return
        
        analyzer = ProfessionalPhotoAnalyzer(self.original_image, self.update_display, self.current_image_path, self.exif_tool_installed)
        self.analysis = analyzer.analyze_composition()
        self.update_results()
    
    def update_display(self, step_name, overlay):
        self.show_image(overlay)
        self.results_text.insert(tk.END, f"\nCompleted: {step_name}\n")
        self.results_text.see(tk.END)
        self.root.update()
        time.sleep(0.5)  # Pause for visualization
    
    def update_results(self):
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "\nFINAL ANALYSIS REPORT\n")
        self.results_text.insert(tk.END, "="*40 + "\n")
        
        # Technical Analysis
        self.results_text.insert(tk.END, "\nTECHNICAL ANALYSIS:\n")
        self.results_text.insert(tk.END, f"Exposure: {self.analysis['technical']['exposure']}\n")
        self.results_text.insert(tk.END, f"Motion Blur: {self.analysis['technical']['motion_blur']}\n")
        self.results_text.insert(tk.END, f"Brightness: {self.analysis['technical']['brightness']}\n")
        self.results_text.insert(tk.END, f"Histogram Span: {self.analysis['technical']['histogram_span']}\n")
        
        # Metadata Analysis
        self.results_text.insert(tk.END, "\nCAMERA METADATA:\n")
        if self.analysis['metadata']:
            self.results_text.insert(tk.END, f"Camera: {self.analysis['metadata']['Camera']}\n")
            self.results_text.insert(tk.END, f"Focal Length: {self.analysis['metadata']['FocalLength']}\n")
            self.results_text.insert(tk.END, f"Aperture: {self.analysis['metadata']['Aperture']}\n")
        else:
            if not self.exif_tool_installed:
                self.results_text.insert(tk.END, "ExifTool not installed. Metadata extraction skipped.\n")
                self.results_text.insert(tk.END, "Install ExifTool from https://exiftool.org/ for metadata support.\n")
            else:
                self.results_text.insert(tk.END, "No metadata found.\n")
        
        # Face Analysis - Updated label
        self.results_text.insert(tk.END, "\nFACE ANALYSIS:\n")
        self.results_text.insert(tk.END, f"Front Facing Faces Detected: {len(self.analysis['faces'])}\n")
        for idx, face in enumerate(self.analysis['faces']):
            self.results_text.insert(tk.END, 
                f"Face {idx+1}: Focus {'Good' if face['focused'] else 'Needs Improvement'} "
                f"(Score: {face['focus_score']}/200)\n")
        
        # Contrast Analysis
        self.results_text.insert(tk.END, "\nCONTRAST ANALYSIS:\n")
        self.results_text.insert(tk.END, f"Dynamic Range: {self.analysis['contrast']['dynamic_range']}/255\n")
        self.results_text.insert(tk.END, f"Recommendation: {self.analysis['contrast']['recommendation']}\n")
        
        # Noise Analysis
        self.results_text.insert(tk.END, "\nNOISE ANALYSIS:\n")
        self.results_text.insert(tk.END, f"Noise Level: {self.analysis['noise']['level']}% \n")
        self.results_text.insert(tk.END, f"Recommendation: {self.analysis['noise']['recommendation']}\n")
        
       
        # Crop Suggestions
        self.results_text.insert(tk.END, "\nCROP SUGGESTIONS:\n")
        for crop in self.analysis['crop_suggestions']:
            self.results_text.insert(tk.END, f"- {crop['name']}\n")
            self.results_text.insert(tk.END, f"  Description: {crop['description']}\n")
            self.results_text.insert(tk.END, f"  Coordinates: {crop['coords']}\n")
        
        # Leading Lines
        self.results_text.insert(tk.END, "\nCOMPOSITION ANALYSIS:\n")
        self.results_text.insert(tk.END, f"Leading Lines Found: {self.analysis['leading_lines']['count']}\n")
        self.results_text.insert(tk.END, f"Recommendation: {self.analysis['leading_lines']['recommendation']}\n")

class ProfessionalPhotoAnalyzer:
    def __init__(self, image, display_callback, image_path, exif_tool_installed):
        self.image = image
        self.h, self.w = image.shape[:2]
        self.gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        self.display = display_callback
        self.image_path = image_path
        self.exif_tool_installed = exif_tool_installed
        self.analysis = {
            'contrast': {},
            'noise': {},
            'technical': {},
            'faces': [],
            'crop_suggestions': [],
            'leading_lines': {},
            'metadata': {}
        }
        self.metadata = self._extract_metadata()
        self.analysis['metadata'] = self.metadata
        self.face_net = cv2.dnn.readNetFromCaffe(
            os.path.join(os.path.dirname(__file__), "deploy.prototxt"),
            os.path.join(os.path.dirname(__file__), "res10_300x300_ssd_iter_140000.caffemodel")
        )

    def _extract_metadata(self):
        """Extract metadata using exiftool if installed, otherwise skip."""
        metadata = {'Camera': 'N/A', 'FocalLength': 'N/A', 'Aperture': 'N/A'}
        
        if not self.exif_tool_installed:
            return metadata  # Skip metadata extraction
        
        try:
            # Use exiftool to extract all metadata
            with exiftool.ExifToolHelper() as et:
                meta = et.get_metadata(self.image_path)[0]  # Get metadata for the first file
                
                # Extract camera model
                metadata['Camera'] = meta.get('EXIF:Model', 
                    meta.get('MakerNotes:Model', 
                    meta.get('QuickTime:Model', 'N/A')))
                
                # Extract focal length
                focal_length = meta.get('EXIF:FocalLength', 
                    meta.get('MakerNotes:FocalLength', 'N/A'))
                if isinstance(focal_length, str) and 'mm' in focal_length:
                    metadata['FocalLength'] = focal_length
                elif isinstance(focal_length, (int, float)):
                    metadata['FocalLength'] = f"{focal_length}mm"
                
                # Extract aperture (handle different formats)
                aperture = meta.get('EXIF:FNumber', 
                    meta.get('EXIF:ApertureValue', 
                    meta.get('MakerNotes:Aperture', 'N/A')))
                
                if isinstance(aperture, float):
                    metadata['Aperture'] = f"ƒ/{aperture:.1f}"
                elif isinstance(aperture, str) and '/' in aperture:
                    parts = aperture.split('/')
                    if len(parts) == 2:
                        metadata['Aperture'] = f"ƒ/{float(parts[0])/float(parts[1]):.1f}"
                elif aperture != 'N/A':
                    metadata['Aperture'] = f"ƒ/{float(aperture):.1f}"

        except Exception as e:
            logging.error(f"Metadata error: {str(e)}")
        
        return metadata


    def analyze_composition(self):
        try:
            self.display("Initializing...", {})
            self._analyze_technical()
            self._analyze_contrast()
            self._analyze_noise()
            self._detect_faces()
            self._analyze_leading_lines()
            self._generate_crop_suggestions()
        except Exception as e:
            logging.error(f"Analysis error: {str(e)}")
        return self.analysis

    def _analyze_technical(self):
        """Complete technical analysis with blur detection"""
        hist = cv2.calcHist([self.gray], [0], None, [256], [0,256])
        hist_norm = hist.ravel()/hist.sum()
        q = np.cumsum(hist_norm)
        under = np.argmax(q > 0.02)
        over = np.argmax(q > 0.98)
        avg_brightness = np.mean(self.gray)
        
        # Exposure evaluation
        exposure_status = "Good exposure" if 50 < avg_brightness < 200 else \
                         "Potential underexposure" if avg_brightness <= 50 else \
                         "Potential overexposure"
        
        # Motion blur detection
        laplacian_var = cv2.Laplacian(self.gray, cv2.CV_64F).var()
        motion_status = "Significant motion blur" if laplacian_var < 100 else \
                        "Possible motion blur" if laplacian_var < 200 else \
                        "Sharp image"
        
        self.analysis['technical'] = {
            'exposure': exposure_status,
            'motion_blur': motion_status,
            'laplacian_var': f"{laplacian_var:.1f}",
            'brightness': f"{avg_brightness:.1f}",
            'histogram_span': f"{under}-{over}"
        }

    def _analyze_contrast(self):
        """Analyze image contrast"""
        hist = cv2.calcHist([self.gray], [0], None, [256], [0, 256])
        cdf = hist.cumsum()
        low = np.where(cdf > 0.02 * cdf.max())[0][0]
        high = np.where(cdf > 0.98 * cdf.max())[0][0]
        dynamic_range = high - low
        
        rec = "Good dynamic range" if dynamic_range > 180 else \
              "Moderate dynamic range" if dynamic_range > 120 else \
              "Low dynamic range - consider histogram expansion"
        
        self.analysis['contrast'] = {
            'dynamic_range': dynamic_range,
            'recommendation': rec
        }
        self.display("Contrast Analysis", {})

    def _analyze_noise(self):
        """Analyze image noise"""
        denoised = cv2.fastNlMeansDenoising(self.gray, None, 20, 7, 21)
        noise = cv2.absdiff(self.gray, denoised)
        noise_level = (np.std(noise) / 255) * 100
        
        rec = "Clean image" if noise_level < 5 else \
              "Moderate noise - optional denoising" if noise_level < 15 else \
              "High noise - recommend denoising"
        
        self.analysis['noise'] = {
            'level': f"{noise_level:.1f}",
            'recommendation': rec
        }
        self.display("Noise Analysis", {})

    def _detect_faces(self):
        """Detect faces and analyze focus"""
        blob = cv2.dnn.blobFromImage(cv2.resize(self.image, (300, 300)), 1.0,
                                    (300, 300), (104.0, 177.0, 123.0))
        self.face_net.setInput(blob)
        detections = self.face_net.forward()
        
        faces = []
        overlay = {'faces': []}
        
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            if confidence > 0.5:
                box = detections[0, 0, i, 3:7] * np.array([self.w, self.h, self.w, self.h])
                x1, y1, x2, y2 = box.astype("int")
                w, h = x2 - x1, y2 - y1
                
                # Focus analysis
                face_roi = self.gray[y1:y2, x1:x2]
                if face_roi.size == 0:
                    continue
                focus_score = cv2.Laplacian(face_roi, cv2.CV_64F).var()
                
                face_data = {
                    'rect': (x1, y1, w, h),
                    'focus_score': f"{focus_score:.1f}",
                    'focused': focus_score > 150
                }
                faces.append(face_data)
                overlay['faces'].append(((x1, y1, w, h), focus_score > 150))
                
                self.display("Face Detection", overlay)
                time.sleep(0.5)
        
        self.analysis['faces'] = faces

    def _detect_main_subject(self):
        """Detect the main subject using saliency, faces, and edge density"""
        subject_info = {
            'center': (self.w//2, self.h//2),
            'weight': 0.5,
            'type': 'generic'
        }

        # 1. Saliency-based detection
        saliency = cv2.saliency.StaticSaliencyFineGrained_create()
        success, saliency_map = saliency.computeSaliency(self.image)
        if success:
            _, saliency_thresh = cv2.threshold((saliency_map*255).astype(np.uint8), 200, 255, cv2.THRESH_BINARY)
            saliency_contours, _ = cv2.findContours(saliency_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if saliency_contours:
                largest_saliency = max(saliency_contours, key=cv2.contourArea)
                M = cv2.moments(largest_saliency)
                if M["m00"] > 0:
                    saliency_center = (int(M["m10"]/M["m00"]), int(M["m01"]/M["m00"]))
                    subject_info['center'] = saliency_center
                    subject_info['weight'] = 0.7
                    subject_info['type'] = 'salient_object'

        # 2. Face detection priority
        if self.analysis['faces']:
            main_face = self.analysis['faces'][0]['rect']
            face_center = (main_face[0] + main_face[2]//2, main_face[1] + main_face[3]//2)
            subject_info['center'] = face_center
            subject_info['weight'] = 1.0  # Faces get highest priority
            subject_info['type'] = 'face'

        # 3. Edge density analysis
        edges = cv2.Canny(self.gray, 100, 200)
        edge_density = cv2.resize(edges, (10, 10)) / 255.0
        max_edge = np.unravel_index(np.argmax(edge_density), edge_density.shape)
        edge_center = (int((max_edge[1]+0.5)*self.w/10), int((max_edge[0]+0.5)*self.h/10))
        
        # Combine results
        if subject_info['weight'] < 0.8:
            subject_info['center'] = (
                int(subject_info['center'][0]*0.7 + edge_center[0]*0.3),
                int(subject_info['center'][1]*0.7 + edge_center[1]*0.3)
            )
            subject_info['type'] = 'edge_based'

        return subject_info

    def _analyze_leading_lines(self):
        """Detect leading lines in the image"""
        scale_factor = 800 / max(self.w, self.h)
        resized_w = int(self.w * scale_factor)
        resized_h = int(self.h * scale_factor)
        resized_gray = cv2.resize(self.gray, (resized_w, resized_h))

        # Edge detection
        median = np.median(resized_gray)
        lower = int(max(0, 0.7 * median))
        upper = int(min(255, 1.3 * median))
        edges = cv2.Canny(resized_gray, lower, upper)

        # Probabilistic Hough Transform
        lines = cv2.HoughLinesP(edges, 
                               rho=1, 
                               theta=np.pi/180, 
                               threshold=50, 
                               minLineLength=int(resized_w * 0.15), 
                               maxLineGap=int(resized_w * 0.02))

        # Filter and scale lines back to original size
        final_lines = []
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                x1 = int(x1 / scale_factor)
                y1 = int(y1 / scale_factor)
                x2 = int(x2 / scale_factor)
                y2 = int(y2 / scale_factor)
                
                length = np.sqrt((x2-x1)**2 + (y2-y1)**2)
                angle = np.abs(np.arctan2(y2-y1, x2-x1) * 180/np.pi)
                
                if (length > self.w * 0.2 and 30 < angle < 150 and 
                    self._is_meaningful_line(x1, y1, x2, y2)):
                    final_lines.append((x1, y1, x2, y2))

        # Remove redundant lines
        final_lines = self._non_max_suppression(final_lines)
        
        # Analysis results
        rec = "Strong leading lines" if len(final_lines) >= 2 else \
              "Could use more directional elements" if len(final_lines) >= 1 else \
              "Lack of strong compositional lines"
        
        self.analysis['leading_lines'] = {
            'count': len(final_lines),
            'lines': final_lines,
            'recommendation': rec
        }
        self.display("Leading Lines", {'lines': final_lines})

    def _is_meaningful_line(self, x1, y1, x2, y2):
        """Check if line has significant contrast difference from surroundings"""
        steps = 5
        dx = (x2 - x1) / steps
        dy = (y2 - y1) / steps
        
        contrasts = []
        for i in range(steps):
            px = int(x1 + i*dx)
            py = int(y1 + i*dy)
            if 0 <= px < self.w and 0 <= py < self.h:
                area = self.gray[py-2:py+3, px-2:px+3]
                if area.size > 0:
                    contrasts.append(np.std(area))
        
        return np.mean(contrasts) > 25 if contrasts else False

    def _non_max_suppression(self, lines, eps=30):
        """Remove overlapping lines using distance-based suppression"""
        if len(lines) == 0:
            return []
        
        lines = np.array(lines)
        midpoints = np.array([[(x1+x2)/2, (y1+y2)/2] for x1,y1,x2,y2 in lines])
        angles = np.array([np.arctan2(y2-y1, x2-x1) for x1,y1,x2,y2 in lines])
        
        remaining = list(range(len(lines)))
        final = []
        
        while len(remaining) > 0:
            idx = remaining[0]
            current_line = lines[idx]
            
            angle_diff = np.abs(angles - angles[idx])
            dist_diff = np.linalg.norm(midpoints - midpoints[idx], axis=1)
            
            similar = (angle_diff < 15) & (dist_diff < eps)
            similar_indices = np.where(similar)[0]
            
            cluster_lines = lines[similar_indices]
            lengths = [np.sqrt((x2-x1)**2 + (y2-y1)**2) for x1,y1,x2,y2 in cluster_lines]
            best_idx = np.argmax(lengths)
            final.append(tuple(cluster_lines[best_idx]))
            
            remaining = [i for i in remaining if i not in similar_indices]
        
        return final

    def _generate_crop_suggestions(self):
        """Generate crop suggestions based on subject and composition"""
        subject = self._detect_main_subject()
        subj_x, subj_y = subject['center']
        crops = []
        
        # 1. Subject-Centered Crop
        crop_size = int(min(self.w, self.h) * 0.4)
        x1 = max(0, subj_x - crop_size//2)
        y1 = max(0, subj_y - crop_size//2)
        x2 = min(self.w, x1 + crop_size)
        y2 = min(self.h, y1 + crop_size)
        crops.append({
            'name': "Subject-Centered Framing",
            'coords': (x1, y1, x2, y2),
            'description': f"Tight crop around the main {subject['type']} (detected at {subject['center']})"
        })

        # 2. Rule of Thirds
        third_x = self.w // 3
        third_y = self.h // 3
        crops.append({
            'name': "Rule of Thirds Composition",
            'coords': (
                max(0, third_x - third_x//2),
                max(0, third_y - third_y//2),
                min(self.w, third_x + third_x//2),
                min(self.h, third_y + third_y//2)
            ),
            'description': "Classic composition with subject placed at intersection points"
        })

        # 3. Leading Lines Emphasis
        if self.analysis['leading_lines']['count'] > 0:
            main_line = self.analysis['leading_lines']['lines'][0]
            crops.append({
                'name': "Leading Line Emphasis",
                'coords': (
                    max(0, main_line[0] - self.w//4),
                    max(0, main_line[1] - self.h//4),
                    min(self.w, main_line[2] + self.w//4),
                    min(self.h, main_line[3] + self.h//4)
                ),
                'description': "Crop to emphasize strongest leading line in composition"
            })

        self.analysis['crop_suggestions'] = crops
        self.display("Crop Suggestions", {'crops': [c['coords'] for c in crops]})

if __name__ == "__main__":
    # Check for exiftool installation
    try:
        subprocess.run(['exiftool', '-ver'], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("\nERROR: ExifTool not installed. Required for metadata extraction.")
        print("Download from https://exiftool.org/ and add to system PATH")
        exit(1)
    
    root = tk.Tk()
    app = PhotoAnalyzerApp(root)
    root.mainloop()