import os
import threading
import requests
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import io
import subprocess
import time

# Fixed image dimensions (same as app.py)
IMAGE_WIDTH = 1600
IMAGE_HEIGHT = 900

def start_flask_server():
    """
    Start the Flask server as a background process if it is not already running.
    """
    try:
        response = requests.get("http://127.0.0.1:5000/test", timeout=3)
        if response.status_code == 200:
            print("Flask server is already running.")
            return
    except requests.ConnectionError:
        print("Flask server is not running. Starting it...")

    def run_server():
        subprocess.run(["python", "app.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Wait for the server to be ready
    for _ in range(10):
        try:
            response = requests.get("http://127.0.0.1:5000/test", timeout=3)
            if response.status_code == 200:
                print("Flask server is up and running.")
                return
        except requests.ConnectionError:
            time.sleep(1)
    raise TimeoutError("Unable to start Flask server.")

def render_latex():
    """
    Render the LaTeX math script and display the image.
    """
    math_script = text_input.get("1.0", "end-1c").strip()

    if not math_script:
        rendered_output.config(image='', width=1, height=1)
        rendered_output.image = None
        return

    def fetch_and_display():
        try:
            # Get the display dimensions
            display_width = image_frame.winfo_width()
            display_height = display_width * 9 / 16  # Maintain 16:9 aspect ratio

            # Set initial font size proportional to display height
            max_font_size = 50
            min_font_size = 10
            font_size = max(min_font_size, int(display_height * 0.08))

            response = requests.post(
                "http://127.0.0.1:5000/render",
                json={
                    "math": math_script,
                    "fileType": "png",
                    "maxWidth": display_width / 100,  # Inches for rendering
                    "maxHeight": display_height / 100,
                    "minFontSize": min_font_size,
                    "maxFontSize": max_font_size,
                    "fontSize": font_size,  # Dynamically calculated font size
                }
            )
            response.raise_for_status()
            img_data = response.content
            global latest_image
            latest_image = img_data
            display_image(img_data)
        except Exception as e:
            print(f"Render Error: {e}")

    threading.Thread(target=fetch_and_display, daemon=True).start()

def display_image(img_data):
    """
    Display the rendered image in the Tkinter UI with a fixed 16:9 aspect ratio.
    """
    try:
        img = Image.open(io.BytesIO(img_data))

        display_width = image_frame.winfo_width()
        display_height = display_width * 9 / 16  # Enforce 16:9 aspect ratio

        scale = min(display_width / IMAGE_WIDTH, display_height / IMAGE_HEIGHT)
        new_width = int(IMAGE_WIDTH * scale)
        new_height = int(IMAGE_HEIGHT * scale)
        img_resized = img.resize((new_width, new_height), Image.LANCZOS)

        photo = ImageTk.PhotoImage(img_resized)
        rendered_output.config(image=photo, width=new_width, height=new_height)
        rendered_output.image = photo
    except Exception as e:
        print(f"Display Error: {e}")

def save_image():
    """
    Save the latest rendered image to a file.
    """
    if latest_image:
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg;*.jpeg"), ("All files", "*.*")]
        )
        if file_path:
            with open(file_path, "wb") as f:
                f.write(latest_image)

def start_ui():
    """
    Start the Tkinter UI.
    """
    global text_input, rendered_output, root, image_frame, latest_image

    root = tk.Tk()
    root.title("LaTeX To Image")
    root.geometry("600x338")  # Default window size (16:9 aspect ratio)
    root.minsize(400, 225)    # Minimum size (16:9 aspect ratio)
    root.configure(bg='white')

    root.columnconfigure(0, weight=1)
    root.rowconfigure(1, weight=1)

    text_input = tk.Text(root, height=6, wrap="word", bg='white', fg='black', insertbackground='black')
    text_input.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
    text_input.focus_set()

    render_after_id = None

    def on_key_release(event):
        nonlocal render_after_id
        if render_after_id:
            root.after_cancel(render_after_id)
        render_after_id = root.after(250, render_latex)

    text_input.bind("<KeyRelease>", on_key_release)

    image_frame = tk.Frame(root, bg='white')
    image_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
    image_frame.columnconfigure(0, weight=1)
    image_frame.rowconfigure(0, weight=1)

    rendered_output = tk.Label(image_frame, background='white')
    rendered_output.grid(row=0, column=0)

    save_button = tk.Button(root, text="Save as Image", command=save_image)
    save_button.grid(row=2, column=0, pady=(5, 10), padx=10, sticky="e")

    latest_image = None

    resize_after_id = None

    def on_resize(event):
        nonlocal resize_after_id
        if resize_after_id:
            root.after_cancel(resize_after_id)
        resize_after_id = root.after(250, render_latex)

    root.bind("<Configure>", on_resize)
    root.mainloop()

if __name__ == '__main__':
    try:
        start_flask_server()
        print("Server is ready. Proceeding to UI...")
        start_ui()
    except TimeoutError as e:
        print(e)
