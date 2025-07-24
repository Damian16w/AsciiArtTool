import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
from PIL import Image, ImageOps, ImageFilter, ImageDraw, ImageEnhance

# ASCII characters used for drawing
ASCIICHARS = "@%#*+=-:. "

# --- Image Processing Functions ---

def resize_image(image, new_width=100):
    """Resize image maintaining aspect ratio for ASCII art."""
    width, height = image.size
    aspect_ratio = height / width
    new_height = int(aspect_ratio * new_width * 0.55)
    return image.resize((new_width, new_height))

def grayify(image):
    """Convert image to grayscale."""
    return image.convert("L")

def pixels_to_ascii(image):
    """Convert grayscale image pixels to ASCII characters."""
    pixels = image.getdata()
    ascii_str = "".join(ASCIICHARS[pixel * (len(ASCIICHARS) - 1) // 255] for pixel in pixels)
    return ascii_str

# --- Filter Definitions ---

FILTERS = {
    "None": lambda img, **kwargs: img,
    "Grayscale": lambda img, **kwargs: img.convert("L"),
    "Invert": lambda img, threshold=128, **kwargs: ImageOps.invert(img.convert("L").point(lambda p: 255 if p > threshold else 0)),
    "Blur": lambda img, radius=2, **kwargs: img.filter(ImageFilter.GaussianBlur(radius)),
    "Brightness": lambda img, factor=1.0, **kwargs: ImageEnhance.Brightness(img).enhance(factor),
    "Contrast": lambda img, factor=1.0, **kwargs: ImageEnhance.Contrast(img).enhance(factor),
}

FILTER_DEFS = {
    "Grayscale": {},
    "Invert": {"threshold": {"from_": 0, "to": 255, "init": 128}},
    "Blur": {"radius": {"from_": 0, "to": 10, "init": 2, "resolution": 0.1}},
    "Brightness": {"factor": {"from_": 0.1, "to": 3.0, "init": 1.0, "resolution": 0.1}},
    "Contrast": {"factor": {"from_": 0.1, "to": 3.0, "init": 1.0, "resolution": 0.1}},
}

filter_params = {
    "Invert": {"threshold": 128},
    "Blur": {"radius": 2},
    "Brightness": {"factor": 1.0},
    "Contrast": {"factor": 1.0},
}

# --- State Tracking ---

drawn_image = None
last_image_path = None
last_drawn_image = None

# --- Main Conversion Logic ---

def apply_all_filters(image):
    """Apply all enabled filters in a fixed order."""
    img = image
    if active_filters["Grayscale"].get():
        img = FILTERS["Grayscale"](img)
    if active_filters["Invert"].get():
        img = FILTERS["Invert"](img, threshold=filter_params["Invert"]["threshold"])
    if active_filters["Blur"].get():
        img = FILTERS["Blur"](img, radius=filter_params["Blur"]["radius"])
    if active_filters["Brightness"].get():
        img = FILTERS["Brightness"](img, factor=filter_params["Brightness"]["factor"])
    if active_filters["Contrast"].get():
        img = FILTERS["Contrast"](img, factor=filter_params["Contrast"]["factor"])
    return img

def convert_image_to_ascii(image_path=None, new_width=100, pil_image=None):
    """Convert an image (from file or PIL) to ASCII art string."""
    try:
        image = pil_image if pil_image is not None else Image.open(image_path)
    except Exception:
        return "Error: Unable to open image file."
    image = resize_image(image, new_width)
    image = apply_all_filters(image)
    image = grayify(image)
    ascii_str = pixels_to_ascii(image)
    img_width = image.width
    ascii_img = '\n'.join(ascii_str[i:(i + img_width)] for i in range(0, len(ascii_str), img_width))
    return ascii_img

# --- GUI Functions ---

def open_image():
    """Open an image file and display its ASCII art."""
    global last_image_path, last_drawn_image
    file_path = filedialog.askopenfilename()
    if file_path:
        ascii_art = convert_image_to_ascii(file_path, new_width=100)
        textBox.delete(1.0, tk.END)
        textBox.insert(tk.END, ascii_art)
        last_image_path = file_path
        last_drawn_image = None

def update_and_refresh(*args):
    """Live update ASCII art when filters or parameters change."""
    if last_drawn_image is not None:
        ascii_art = convert_image_to_ascii(pil_image=last_drawn_image, new_width=100)
        textBox.delete(1.0, tk.END)
        textBox.insert(tk.END, ascii_art)
    elif last_image_path is not None:
        ascii_art = convert_image_to_ascii(last_image_path, new_width=100)
        textBox.delete(1.0, tk.END)
        textBox.insert(tk.END, ascii_art)

def copy_to_clipboard():
    """Copy ASCII art to clipboard."""
    ascii_art = textBox.get(1.0, tk.END)
    root.clipboard_clear()
    root.clipboard_append(ascii_art)
    messagebox.showinfo("Copied", "ASCII art copied to clipboard!")

def open_draw_window():
    """Open a window for drawing your own image."""
    root.update_idletasks()
    main_w = root.winfo_width()
    main_h = root.winfo_height()
    canvas_width = max(100, int(main_w * 0.8))
    canvas_height = max(80, int(main_h * 0.5))

    drawWin = tk.Toplevel(root)
    drawWin.title("Draw Image")
    drawWin.configure(bg="#101010")
    drawWin.geometry(f"{canvas_width+20}x{canvas_height+90}")

    # Make the draw window and canvas resizable
    drawWin.rowconfigure(1, weight=1)
    drawWin.columnconfigure(0, weight=1)

    # Canvas frame for proper resizing
    canvas_frame = tk.Frame(drawWin, bg="#101010")
    canvas_frame.grid(row=1, column=0, sticky="nsew")
    canvas = tk.Canvas(canvas_frame, width=canvas_width, height=canvas_height, bg="#101010", highlightbackground="#00FF00")
    canvas.pack(fill=tk.BOTH, expand=True)

    img = Image.new("L", (canvas_width, canvas_height), 255)
    draw = ImageDraw.Draw(img)
    last = [None]

    # Brush controls
    controls = tk.Frame(drawWin, bg="#101010")
    controls.grid(row=0, column=0, pady=5, sticky="ew")

    brush_size_var = tk.IntVar(value=3)
    eraser_mode = tk.BooleanVar(value=False)

    mode_label = tk.Label(
        controls, text="Brush", bg="#101010", fg="#00FF00", font=("Courier", 10, "bold"), width=8
    )
    mode_label.pack(side=tk.LEFT, padx=(0, 10))

    def set_brush_size(val):
        brush_size_var.set(int(float(val)))

    def toggle_eraser():
        eraser_mode.set(not eraser_mode.get())
        btn_eraser.config(relief=tk.SUNKEN if eraser_mode.get() else tk.RAISED)
        if eraser_mode.get():
            mode_label.config(text="Eraser", fg="#00FF00", bg="#003300")
        else:
            mode_label.config(text="Brush", fg="#00FF00", bg="#101010")

    tk.Label(controls, text="Brush size:", bg="#101010", fg="#00FF00").pack(side=tk.LEFT, padx=(0, 5))
    brush_slider = tk.Scale(
        controls, from_=1, to=20, orient=tk.HORIZONTAL, variable=brush_size_var,
        bg="#101010", fg="#00FF00", troughcolor="#003300", highlightbackground="#00FF00",
        activebackground="#00FF00", length=100, width=10, sliderrelief=tk.FLAT, command=set_brush_size
    )
    brush_slider.pack(side=tk.LEFT, padx=(0, 10))

    btn_eraser = tk.Button(
        controls, text="Eraser", command=toggle_eraser,
        bg="#101010", fg="#00FF00", activebackground="#00FF00", activeforeground="#101010",
        highlightbackground="#00FF00", relief=tk.RAISED
    )
    btn_eraser.pack(side=tk.LEFT, padx=(0, 10))

    def draw_callback(event):
        if last[0] is not None:
            x1, y1 = last[0]
            x2, y2 = event.x, event.y
            color = 255 if eraser_mode.get() else 0
            canvas.create_line(x1, y1, x2, y2, fill="#101010" if eraser_mode.get() else "black", width=brush_size_var.get())
            draw.line([x1, y1, x2, y2], fill=color, width=brush_size_var.get())
        last[0] = (event.x, event.y)

    def reset_last(event):
        last[0] = None

    def save_and_convert():
        global drawn_image, last_drawn_image, last_image_path
        drawn_image = img.copy()
        last_drawn_image = drawn_image
        last_image_path = None
        ascii_art = convert_image_to_ascii(pil_image=drawn_image, new_width=100)
        textBox.delete(1.0, tk.END)
        textBox.insert(tk.END, ascii_art)
        drawWin.destroy()

    canvas.bind("<B1-Motion>", draw_callback)
    canvas.bind("<ButtonRelease-1>", reset_last)
    btn_save = tk.Button(
        drawWin, text="Convert to ASCII", command=save_and_convert,
        bg="#101010", fg="#00FF00", activebackground="#00FF00", activeforeground="#101010", highlightbackground="#00FF00"
    )
    btn_save.grid(row=2, column=0, pady=5)

    # Handle resizing: update canvas size and PIL image
    def on_resize(event):
        new_w = max(10, event.width)
        new_h = max(10, event.height)
        # Resize the canvas widget
        canvas.config(width=new_w, height=new_h)
        # Resize the PIL image and drawing context
        nonlocal img, draw
        old_img = img
        img = old_img.resize((new_w, new_h))
        draw = ImageDraw.Draw(img)
        # Redraw the canvas background
        canvas.delete("all")

    canvas.bind("<Configure>", on_resize)

# --- GUI Setup ---

root = tk.Tk()
root.title("ASCII Art Tool - Matrix Edition")
root.configure(bg="#101010")

# Set window icon (favicon) using PNG (works for Tk >= 8.6)
try:
    import sys
    from PIL import ImageTk
    logo_img = Image.open("ASCIILogo2.png")
    logo_tk = ImageTk.PhotoImage(logo_img)
    root.iconphoto(True, logo_tk)
except Exception:
    pass  # Ignore if icon file is missing or incompatible

active_filters = {
    "Grayscale": tk.BooleanVar(value=False, master=root),
    "Invert": tk.BooleanVar(value=False, master=root),
    "Blur": tk.BooleanVar(value=False, master=root),
    "Brightness": tk.BooleanVar(value=False, master=root),
    "Contrast": tk.BooleanVar(value=False, master=root),
}

# Layout: filters on the left, output on the right
main_frame = tk.Frame(root, bg="#101010")
main_frame.pack(fill=tk.BOTH, expand=True)

filtersFrame = tk.Frame(main_frame, bg="#101010", highlightbackground="#00FF00", highlightthickness=2)
filtersFrame.pack(side=tk.LEFT, fill=tk.Y, padx=(10, 0), pady=10)

outputFrame = tk.Frame(main_frame, bg="#101010")
outputFrame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 10), pady=10)

frame = tk.Frame(outputFrame, bg="#101010")
frame.pack(fill=tk.X, pady=(0, 10))

btn = tk.Button(frame, text="Open Image", command=open_image, bg="#101010", fg="#00FF00", activebackground="#00FF00", activeforeground="#101010", highlightbackground="#00FF00")
btn.pack(side=tk.LEFT, padx=2)

btn_draw = tk.Button(frame, text="Draw Image", command=open_draw_window, bg="#101010", fg="#00FF00", activebackground="#00FF00", activeforeground="#101010", highlightbackground="#00FF00")
btn_draw.pack(side=tk.LEFT, padx=2)

btn_copy = tk.Button(frame, text="Copy to Clipboard", command=copy_to_clipboard, bg="#101010", fg="#00FF00", activebackground="#00FF00", activeforeground="#101010", highlightbackground="#00FF00")
btn_copy.pack(side=tk.LEFT, padx=2)

def make_filter_row(filter_name, params):
    row = tk.Frame(filtersFrame, bg="#101010")
    cb = tk.Checkbutton(
        row, text=filter_name, variable=active_filters[filter_name], command=update_and_refresh,
        bg="#101010", fg="#00FF00", selectcolor="#003300", activebackground="#101010",
        activeforeground="#00FF00", highlightbackground="#00FF00", width=10, anchor="w", padx=5
    )
    cb.grid(row=0, column=0, sticky="w", padx=(0, 5))
    col = 1
    for param, opts in params.items():
        lbl = tk.Label(row, text=f"{param.capitalize()}:", bg="#101010", fg="#00FF00", width=10, anchor="e")
        lbl.grid(row=0, column=col, sticky="e", padx=(0, 2))
        col += 1
        var = tk.DoubleVar(value=opts.get("init", 1.0), master=root)
        if filter_name in filter_params and param in filter_params[filter_name]:
            filter_params[filter_name][param] = opts.get("init", 1.0)
        def make_update_fn(fname, pname, v):
            def fn(val):
                filter_params[fname][pname] = float(val)
                update_and_refresh()
            return fn
        scale = tk.Scale(
            row,
            from_=opts.get("from_", 0),
            to=opts.get("to", 1),
            resolution=opts.get("resolution", 1),
            orient=tk.HORIZONTAL,
            variable=var,
            command=make_update_fn(filter_name, param, var),
            length=120,
            bg="#101010",
            fg="#00FF00",
            troughcolor="#003300",
            highlightbackground="#00FF00",
            activebackground="#00FF00",
            sliderrelief=tk.FLAT
        )
        scale.grid(row=0, column=col, sticky="w", padx=(0, 10))
        col += 1
    row.pack(anchor="w", pady=2, fill=tk.X, padx=2)

for fname, params in FILTER_DEFS.items():
    make_filter_row(fname, params)

textBox = scrolledtext.ScrolledText(
    outputFrame, wrap=tk.WORD, width=100, height=40, font=("Courier", 6),
    bg="#101010", fg="#00FF00", insertbackground="#00FF00", selectbackground="#003300",
    selectforeground="#00FF00", borderwidth=2, relief=tk.SUNKEN
)
textBox.pack(fill=tk.BOTH, expand=True)

# Copyright notice
copyright_label = tk.Label(
    root,
    text="© 2025 Ascii Art Tool by DrJunkHoofd | :3",
    bg="#101010",
    fg="#00FF00",
    font=("Courier", 8)
)
copyright_label.pack(side=tk.BOTTOM, pady=(0, 2))

root.mainloop()