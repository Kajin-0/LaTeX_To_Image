import os
import subprocess
import time
import requests
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk, ImageOps
import io

def start_flask_server():
    """
    Start the Flask server as a subprocess if it is not already running.
    """
    try:
        # Check if the server is already running
        response = requests.get("http://127.0.0.1:5000/test", timeout=5)
        if response.status_code == 200:
            print("Flask server is already running.")
            return None  # No process to return since the server is already running
    except requests.ConnectionError:
        print("Flask server is not running. Starting it...")

    # Ensure the working directory is correct
    os.chdir(os.path.dirname(__file__))

    # Start Flask server as a subprocess
    process = subprocess.Popen(
        ["python", "app.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    return process

def check_server(timeout=30):
    """
    Wait until the Flask server is ready or until the timeout is reached.
    """
    url = "http://127.0.0.1:5000/test"
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print("Flask server is up and running.")
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(1)  # Poll every 1 second
    raise TimeoutError("Unable to connect to the Flask server within the timeout period.")

def render_latex():
    """
    Render the LaTeX math script and display the image.
    """
    math_script = text_input.get("1.0", "end-1c").strip()

    if not math_script:
        # Clear the image if input is empty
        rendered_output.config(image='', width=1, height=1)
        rendered_output.image = None
        return

    try:
        # Get the available display area
        display_width = image_frame.winfo_width()
        display_height = display_width * 9 / 16  # Adjust height for 16:9 aspect ratio

        # Send the display dimensions and font size range to the server
        response = requests.post(
            "http://127.0.0.1:5000/render",
            json={
                "math": math_script,
                "fileType": "png",
                "maxWidth": display_width / 100,  # Convert pixels to inches (assuming 100 DPI)
                "maxHeight": display_height / 100,
                "minFontSize": 10,
                "maxFontSize": 50
            }
        )
        response.raise_for_status()
        img_data = response.content

        # Update the cached image
        global latest_image
        latest_image = img_data

        # Display the image
        display_image(img_data)
    except requests.exceptions.RequestException as e:
        # Silently handle the error without showing a popup
        print(f"Render Error: {e}")
        # Do not clear the image; keep displaying the last successful render
        # Optionally, you can indicate an error visually if desired
        pass

def display_image(img_data):
    """
    Display the rendered image in the Tkinter UI.
    """
    try:
        img = Image.open(io.BytesIO(img_data))

        # Add a border directly to the image
        border_color = '#CCCCCC'  # Muted grey color
        img_with_border = ImageOps.expand(img, border=1, fill=border_color)

        # Get the available display area inside the image_frame
        display_width = image_frame.winfo_width()
        display_height = display_width * 9 / 16  # Enforce 16:9 aspect ratio

        # Calculate scaling to fit the image within the display area while maintaining aspect ratio
        width_ratio = display_width / img_with_border.width
        height_ratio = display_height / img_with_border.height
        scale = min(width_ratio, height_ratio, 1.0)

        # Resize image only if necessary
        new_width = int(img_with_border.width * scale)
        new_height = int(img_with_border.height * scale)
        img_resized = img_with_border.resize((new_width, new_height), Image.LANCZOS)

        photo = ImageTk.PhotoImage(img_resized)
        rendered_output.config(image=photo, width=new_width, height=new_height)
        rendered_output.image = photo
    except Exception as e:
        print(f"Display Error: {e}")
        # Silently handle the error without showing a popup
        # Do not clear the image; keep displaying the last successful render
        pass

def save_image():
    """
    Save the latest rendered image to a file.
    """
    if latest_image:
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg;*.jpeg"),
                ("All files", "*.*")
            ]
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
    root.title("LaTeX Math Renderer")
    root.geometry("450x338")  # Set window size
    root.minsize(300, 225)     # Minimum window size
    root.configure(bg='white')

    # Configure the root grid to be expandable
    root.columnconfigure(0, weight=1)
    root.rowconfigure(1, weight=1)  # Make the image_frame expandable

    # Text input for LaTeX script
    text_input = tk.Text(root, height=6, wrap="word", bg='white', fg='black', insertbackground='black')
    text_input.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
    text_input.focus_set()

    # Debounce variables
    render_after_id = None

    def on_key_release(event):
        nonlocal render_after_id
        if render_after_id is not None:
            root.after_cancel(render_after_id)
        render_after_id = root.after(300, render_latex)

    text_input.bind("<KeyRelease>", on_key_release)

    # Frame to contain the rendered image
    image_frame = tk.Frame(root, bg='white')
    image_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
    image_frame.columnconfigure(0, weight=1)
    image_frame.rowconfigure(0, weight=1)

    # Label to display the rendered image
    rendered_output = tk.Label(image_frame, background='white')
    rendered_output.grid(row=0, column=0)

    # Save button aligned to the right
    save_button = tk.Button(root, text="Save as Image", command=save_image)
    save_button.grid(row=2, column=0, pady=(5, 10), padx=10, sticky="e")

    latest_image = None

    # Debounce for resizing
    resize_after_id = None

    def on_resize(event):
        nonlocal resize_after_id
        if resize_after_id is not None:
            root.after_cancel(resize_after_id)
        resize_after_id = root.after(300, render_latex)  # 300ms debounce for resizing

    root.bind("<Configure>", on_resize)

    root.mainloop()

if __name__ == '__main__':
    process = None
    try:
        # Start the Flask server
        process = start_flask_server()

        # Check if the server is ready
        check_server()

        print("Server is ready. Proceeding to UI...")
        # Start the Tkinter UI
        start_ui()
    except TimeoutError as e:
        print(e)
    finally:
        # Cleanup: Ensure subprocess is terminated if it was started
        if process:
            process.terminate()
