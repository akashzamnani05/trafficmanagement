import tkinter as tk
from PIL import Image, ImageTk, ImageOps, ImageFilter
import cv2
from yolo_implementation import YOLOImplementation
from model import run_model

# ---------------------
# Traffic Light Class
# ---------------------
class TrafficLight:
    def __init__(self, parent):
        # Create a fixed-size canvas for the traffic light (60x180)
        self.canvas = tk.Canvas(parent, width=60, height=180, bg="white")
        self.canvas.pack(expand=True, fill=tk.BOTH)
        self.create_lights()

    def create_lights(self):
        # Draw a black rectangle with three circular lights.
        self.canvas.create_rectangle(10, 10, 50, 170, fill="black", outline="black")
        self.red = self.canvas.create_oval(15, 20, 45, 50, fill="gray", outline="black")
        self.yellow = self.canvas.create_oval(15, 55, 45, 85, fill="gray", outline="black")
        self.green = self.canvas.create_oval(15, 90, 45, 120, fill="gray", outline="black")

    def update_light(self, state):
        # Reset lights to gray then highlight the selected one.
        self.canvas.itemconfig(self.red, fill="gray")
        self.canvas.itemconfig(self.yellow, fill="gray")
        self.canvas.itemconfig(self.green, fill="gray")
        if state == "red":
            self.canvas.itemconfig(self.red, fill="red")
        elif state == "green":
            self.canvas.itemconfig(self.green, fill="green")


# ---------------------
# Global Variables
# ---------------------
current_video_index = 0
yolo_executed = False
caps = []  # List to hold cv2.VideoCapture objects

# Fallback dimensions for the video display area (left)
DEFAULT_VIDEO_WIDTH = 400
DEFAULT_VIDEO_HEIGHT = 600

# ---------------------
# Video Update Function
# ---------------------
def update_video():
    global current_video_index, yolo_executed, caps
    cap = caps[current_video_index]
    ret, frame = cap.read()

    if ret:
        # Get the current dimensions of the video display area.
        video_width = video_label.winfo_width()
        video_height = video_label.winfo_height()
        if video_width < 10 or video_height < 10:
            video_width, video_height = DEFAULT_VIDEO_WIDTH, DEFAULT_VIDEO_HEIGHT

        orig_h, orig_w = frame.shape[:2]

        # Calculate scaling for the overlay (preserving aspect ratio)
        scale_overlay = min(video_width / orig_w, video_height / orig_h)
        new_overlay_w = int(orig_w * scale_overlay)
        new_overlay_h = int(orig_h * scale_overlay)

        # Calculate scaling for the background (to fill the area)
        scale_bg = max(video_width / orig_w, video_height / orig_h)
        new_bg_w = int(orig_w * scale_bg)
        new_bg_h = int(orig_h * scale_bg)

        # Create the overlay image
        overlay_frame = cv2.resize(frame, (new_overlay_w, new_overlay_h))
        overlay_frame = cv2.cvtColor(overlay_frame, cv2.COLOR_BGR2RGB)
        overlay_pil = Image.fromarray(overlay_frame)

        # Create the blurred background image
        bg_frame = cv2.resize(frame, (new_bg_w, new_bg_h))
        bg_frame = cv2.cvtColor(bg_frame, cv2.COLOR_BGR2RGB)
        bg_pil = Image.fromarray(bg_frame)
        bg_blurred = bg_pil.filter(ImageFilter.GaussianBlur(radius=15))
        bg_final = ImageOps.fit(bg_blurred, (video_width, video_height))

        # Center the overlay on the blurred background
        offset_x = (video_width - new_overlay_w) // 2
        offset_y = (video_height - new_overlay_h) // 2
        bg_final.paste(overlay_pil, (offset_x, offset_y))

        # Convert composite image to PhotoImage and update the label.
        imgtk = ImageTk.PhotoImage(image=bg_final)
        video_label.imgtk = imgtk  # Keep a reference to avoid garbage collection
        video_label.configure(image=imgtk)

        # Update traffic lights: Only the active video gets the green signal.
        for i, tl in enumerate(traffic_lights):
            if i == current_video_index:
                tl.update_light("green")
            else:
                tl.update_light("red")

        # Run YOLO 3 seconds before the video ends (if applicable)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        current_frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
        if current_frame >= total_frames - (fps * 3) and not yolo_executed:
            next_video_index = (current_video_index + 1) % len(video_paths)
            print(f"Running YOLO on next video: {video_paths[next_video_index]}")
            try:
                yolo = YOLOImplementation()
                dict = yolo.execute(video_paths[next_video_index], mask_paths[next_video_index], 0)
                yolo_executed = True
                prediction = run_model(dict)
                print(prediction)

            except Exception as e:
                print(f"YOLO execution error: {e}")

        video_label.after(2, update_video)
    else:
        # When the video ends: reset its position and switch to the next video.
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        traffic_lights[current_video_index].update_light("red")
        current_video_index = (current_video_index + 1) % len(caps)
        yolo_executed = False
        video_label.after(1000, update_video)

def start_video(idx):
    global current_video_index, yolo_executed
    current_video_index = idx
    yolo_executed = False
    # Reset all videos to the beginning.
    for cap in caps:
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    update_video()


# ---------------------
# Crosswalk Drawing Helper Function
# ---------------------
def draw_crosswalk(canvas, x, y, crosswalk_width, crosswalk_height, orientation):
    """
    Draws a crosswalk consisting of 4 white stripes.
    
    orientation: 'horizontal' means stripes are drawn as horizontal rectangles;
                 'vertical' means stripes are drawn as vertical rectangles.
    """
    stripe_count = 4
    gap = 5
    if orientation == 'horizontal':
        # Total available height minus gaps divided among stripes
        stripe_height = (crosswalk_height - (stripe_count - 1) * gap) / stripe_count
        for i in range(stripe_count):
            y0 = y + i * (stripe_height + gap)
            canvas.create_rectangle(x, y0, x + crosswalk_width, y0 + stripe_height, fill="white", outline="")
    else:  # vertical
        stripe_width = (crosswalk_width - (stripe_count - 1) * gap) / stripe_count
        for i in range(stripe_count):
            x0 = x + i * (stripe_width + gap)
            canvas.create_rectangle(x0, y, x0 + stripe_width, y + crosswalk_height, fill="white", outline="")

# ---------------------
# Road Intersection Drawing Function
# ---------------------
def draw_intersection(canvas, width, height):
    """
    Draws a plus-shaped road intersection with:
      - Thick black horizontal and vertical roads,
      - Dashed white center lines,
      - Crosswalks on all four approaches.
    """
    road_thickness = 60  # Total thickness of each road
    dash_pattern = (10, 10)  # Dash pattern for center lines
    road_color = "#333333" 

    center_x = width // 2
    center_y = height // 2

    # Draw horizontal road (covers full width, centered vertically)
    canvas.create_rectangle(0, center_y - road_thickness // 2,
                            width, center_y + road_thickness // 2,
                            fill=road_color, outline="")

    # Draw vertical road (covers full height, centered horizontally)
    canvas.create_rectangle(center_x - road_thickness // 2, 0,
                            center_x + road_thickness // 2, height,
                            fill=road_color, outline="")

    # Draw horizontal dashed center line
    canvas.create_line(0, center_y, width, center_y,
                       fill="white", width=2, dash=dash_pattern)
    # Draw vertical dashed center line
    canvas.create_line(center_x, 0, center_x, height,
                       fill="white", width=2, dash=dash_pattern)

    # Draw Crosswalks:
    # Parameters for crosswalk dimensions
    cw_top_width = 40
    cw_top_height = 27
    cw_side_width = 27
    cw_side_height = 40

    # Top crosswalk (approach from north): horizontal stripes
    draw_crosswalk(canvas,
                   center_x - cw_top_width / 2,
                   center_y - road_thickness // 2 - cw_top_height - 5,
                   cw_top_width,
                   cw_top_height,
                   'horizontal')
    # Bottom crosswalk (approach from south): horizontal stripes
    draw_crosswalk(canvas,
                   center_x - cw_top_width / 2,
                   center_y + road_thickness // 2 + 5,
                   cw_top_width,
                   cw_top_height,
                   'horizontal')
    # Left crosswalk (approach from west): vertical stripes
    draw_crosswalk(canvas,
                   center_x - road_thickness // 2 - cw_side_width - 5,
                   center_y - cw_side_height / 2,
                   cw_side_width,
                   cw_side_height,
                   'vertical')
    # Right crosswalk (approach from east): vertical stripes
    draw_crosswalk(canvas,
                   center_x + road_thickness // 2 + 5,
                   center_y - cw_side_height / 2,
                   cw_side_width,
                   cw_side_height,
                   'vertical')


# ---------------------
# Main Window & Layout
# ---------------------
root = tk.Tk()
root.title("Traffic Light Simulation with Videos")
root.geometry("800x600")

# Use grid with two columns (50% each) via the 'uniform' option.
root.rowconfigure(0, weight=1)
root.columnconfigure(0, weight=1, uniform="group1")
root.columnconfigure(1, weight=1, uniform="group1")

# Left Frame: Video display area (limited to 50% of the screen)
left_frame = tk.Frame(root, bg="black")
left_frame.grid(row=0, column=0, sticky="nsew")
video_label = tk.Label(left_frame, bg="black")
video_label.pack(fill=tk.BOTH, expand=True)

# Right Frame: Container for the road intersection and traffic signals.
right_frame = tk.Frame(root, bg="white")
right_frame.grid(row=0, column=1, sticky="nsew")

# Create a canvas in the right_frame to draw the road intersection.
road_canvas = tk.Canvas(right_frame, bg="white", highlightthickness=0)
road_canvas.place(relwidth=1, relheight=1)
# Lower the canvas so that it stays behind the traffic signal frames.
road_canvas.tk.call('lower', road_canvas._w)

# ---------------------
# Create Traffic Signal Frames (Plus-Shaped Layout)
# ---------------------
tl_frames = []
traffic_lights = []

# Top Traffic Signal
tl_frame_top = tk.Frame(right_frame, width=60, height=180, bg="white")
tl_frame_top.place(x=0, y=0)
tl_frames.append(tl_frame_top)
traffic_lights.append(TrafficLight(tl_frame_top))

# Bottom Traffic Signal
tl_frame_bottom = tk.Frame(right_frame, width=60, height=180, bg="white")
tl_frame_bottom.place(x=0, y=0)
tl_frames.append(tl_frame_bottom)
traffic_lights.append(TrafficLight(tl_frame_bottom))

# Left Traffic Signal
tl_frame_left = tk.Frame(right_frame, width=60, height=180, bg="white")
tl_frame_left.place(x=0, y=0)
tl_frames.append(tl_frame_left)
traffic_lights.append(TrafficLight(tl_frame_left))

# Right Traffic Signal
tl_frame_right = tk.Frame(right_frame, width=60, height=180, bg="white")
tl_frame_right.place(x=0, y=0)
tl_frames.append(tl_frame_right)
traffic_lights.append(TrafficLight(tl_frame_right))

# ---------------------
# Function to Reposition Traffic Signals & Redraw Road Intersection
# ---------------------
def reposition_tl_frames(event):
    width = event.width
    height = event.height
    tl_width = 60
    tl_height = 180
    margin = 20  # Margin from the frame edges

    # Calculate positions for a plus layout:
    top_x = (width - tl_width) // 2
    top_y = margin

    bottom_x = (width - tl_width) // 2
    bottom_y = height - tl_height - margin

    left_x = margin
    left_y = (height - tl_height) // 2

    right_x = width - tl_width - margin
    right_y = (height - tl_height) // 2

    tl_frames[0].place_configure(x=top_x, y=top_y)
    tl_frames[1].place_configure(x=bottom_x, y=bottom_y)
    tl_frames[2].place_configure(x=left_x, y=left_y)
    tl_frames[3].place_configure(x=right_x, y=right_y)

    # Redraw the road intersection on the road_canvas.
    road_canvas.delete("all")
    draw_intersection(road_canvas, width, height)

# Bind the <Configure> event on right_frame to reposition signals and redraw the intersection.
right_frame.bind("<Configure>", reposition_tl_frames)

# ---------------------
# Video & Mask Paths
# ---------------------
video_paths = [
    "vids/23712-337108764_medium.mp4",
    "vids/cars.mp4",
    "vids/23712-337108764_medium.mp4",
    "vids/cars.mp4"
]

mask_paths = [
    "masks/vid1.png",
    "masks/vid2.png",
    "masks/vid1.png",
    "masks/vid2.png"
]


# Create VideoCapture objects for each video.
caps = [cv2.VideoCapture(path) for path in video_paths]

# Start playing the first video.
start_video(0)

# ---------------------
# Window Closing Handler
# ---------------------
def on_closing():
    for cap in caps:
        if cap.isOpened():
            cap.release()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()

