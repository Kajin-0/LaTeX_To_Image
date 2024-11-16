import matplotlib
matplotlib.use('Agg')  # Use the 'Agg' backend for rendering to a canvas (no GUI required)
from flask import Flask, request, send_file
import matplotlib.pyplot as plt
import io

app = Flask(__name__)

# Default Matplotlib font configuration
plt.rcParams.update({
    "text.usetex": False,          # Use built-in math renderer
    "font.family": "sans-serif",   # Default sans-serif font
    "mathtext.fontset": "dejavusans", # Default math fontset
    "figure.dpi": 300,             # High DPI for better quality
    "mathtext.default": "regular", # Set default math text style
})

SUPPORTED_FILE_TYPES = ['png', 'jpg', 'jpeg', 'svg', 'bmp', 'tif', 'tiff']

@app.route('/render', methods=['POST'])
def render_math():
    """
    Render mathematical expressions into high-quality images using
    Matplotlib's built-in math renderer with default font configuration.
    Ensure images maintain a 16:9 aspect ratio.
    """
    data = request.get_json()

    # Extract parameters with default values
    math_script = data.get('math', '').strip()
    file_type = data.get('fileType', 'png').lower()
    max_width = data.get('maxWidth', 10)  # Inches
    max_height = max_width * 9 / 16       # Calculate height for 16:9 aspect ratio
    min_font_size = data.get('minFontSize', 10)
    max_font_size = data.get('maxFontSize', 50)

    if file_type not in SUPPORTED_FILE_TYPES:
        return {"error": f"Unsupported file type: {file_type}"}, 400

    if not math_script:
        return {"error": "Math script cannot be empty"}, 400

    try:
        # Initialize figure
        fig = plt.figure(figsize=(max_width, max_height))
        ax = fig.add_subplot(111)
        ax.axis('off')

        # Adjust font size to fit text within the figure
        font_size_range = range(max_font_size, min_font_size - 1, -2)
        best_font_size = min_font_size

        for font_size in font_size_range:
            ax.clear()
            ax.axis('off')

            # Render the mathematical text
            text = ax.text(0.5, 0.5, f"${math_script}$",
                           ha='center', va='center',
                           fontsize=font_size,
                           transform=ax.transAxes)

            # Measure text dimensions
            fig.canvas.draw()
            bbox = text.get_window_extent(fig.canvas.get_renderer())
            bbox_inches = bbox.transformed(fig.dpi_scale_trans.inverted())

            # Check if text fits within desired dimensions
            if bbox_inches.width <= max_width * 0.9 and bbox_inches.height <= max_height * 0.9:
                best_font_size = font_size
                break

        # Render with the best font size
        ax.clear()
        ax.axis('off')
        ax.text(0.5, 0.5, f"${math_script}$",
                ha='center', va='center',
                fontsize=best_font_size,
                transform=ax.transAxes)

        # Save the figure to an image buffer
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer,
                    format=file_type,
                    dpi=300,
                    bbox_inches='tight',
                    pad_inches=0.2)
        plt.close(fig)
        img_buffer.seek(0)

        # Determine MIME type for response
        mime_type = f"image/{file_type}" if file_type not in ['tif', 'tiff'] else 'image/tiff'
        return send_file(img_buffer, mimetype=mime_type, as_attachment=False)

    except Exception as e:
        return {"error": f"Failed to render image: {str(e)}"}, 500

@app.route('/test', methods=['GET'])
def test():
    """
    A simple test endpoint to verify that the Flask server is running.
    """
    return "Flask server is running!"

if __name__ == '__main__':
    app.run(port=5000, debug=False)
