import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend for rendering
from flask import Flask, request, send_file
import matplotlib.pyplot as plt
import io
import hashlib
import os

app = Flask(__name__)
CACHE_DIR = 'cache'
os.makedirs(CACHE_DIR, exist_ok=True)

# Fixed image dimensions (pixels)
IMAGE_WIDTH = 1600
IMAGE_HEIGHT = 900
DPI = 100  # Resolution in dots per inch (pixels per inch)

@app.route('/render', methods=['POST'])
def render_math():
    """
    Render a mathematical equation using LaTeX and return it as an image.
    """
    data = request.get_json()
    math_script = data.get('math', '').strip()
    file_type = data.get('fileType', 'png').lower()
    max_width = IMAGE_WIDTH / DPI  # Fixed width in inches
    max_height = IMAGE_HEIGHT / DPI  # Fixed height in inches
    initial_font_size = 50  # Starting font size for adjustment
    margin_ratio = 0.1  # 10% margin on all sides

    if not math_script:
        return {"error": "Math script cannot be empty"}, 400

    # Generate a cache key based on input parameters
    cache_key = hashlib.md5(f"{math_script}-{file_type}".encode()).hexdigest()
    cache_path = os.path.join(CACHE_DIR, f"{cache_key}.{file_type}")

    # Serve the cached image if it exists
    if os.path.exists(cache_path):
        return send_file(cache_path, mimetype=f"image/{file_type}")

    try:
        # Initialize figure
        fig = plt.figure(figsize=(max_width, max_height), dpi=DPI)
        ax = fig.add_subplot(111)
        ax.axis('off')  # Remove axes for a clean image

        # Adjust font size to fit text within the image with margins
        for font_size in range(initial_font_size, 10, -2):  # Decrement font size
            ax.clear()
            ax.axis('off')

            # Render the text with the current font size
            text = ax.text(
                0.5, 0.5, f"${math_script}$",
                ha='center', va='center',
                fontsize=font_size,
                transform=ax.transAxes
            )

            # Measure text dimensions
            fig.canvas.draw()
            bbox = text.get_window_extent(fig.canvas.get_renderer())
            text_width = bbox.width / DPI  # Convert to inches
            text_height = bbox.height / DPI

            # Check if the text fits within the margins
            if text_width <= max_width * (1 - 2 * margin_ratio) and text_height <= max_height * (1 - 2 * margin_ratio):
                break

        # Save the rendered image to the cache path
        with open(cache_path, 'wb') as f:
            fig.savefig(f, format=file_type, bbox_inches='tight', pad_inches=margin_ratio)
        plt.close(fig)

        # Serve the cached image
        return send_file(cache_path, mimetype=f"image/{file_type}")
    except Exception as e:
        return {"error": f"Failed to render image: {e}"}, 500

@app.route('/test', methods=['GET'])
def test():
    """
    Test endpoint to verify that the server is running.
    """
    return "Flask server is running!"

if __name__ == '__main__':
    app.run(port=5000, debug=False)
