import pandas as pd
import numpy as np
from PIL import Image, ImageDraw, ImagePath
import streamlit as st
from streamlit_drawable_canvas import st_canvas

from mylib import get_random_ellipse, get_ellipse, get_best_ellipse, get_best_ellipse_alt

stroke_color = "#000"
bg_color = "#fff"

width = 800
height = 600

center = (width / 2, height / 2)


st.sidebar.title("Calculate Button Example")

stroke_width = st.sidebar.slider("Stroke width: ", 1, 25, 3)

if st.sidebar.button("Regenerate ellipse"):
    st.session_state["drawing"] = True
    st.session_state["xy"] = get_random_ellipse(center, 100)

if st.sidebar.button("Calculate"):
    st.session_state["drawing"] = False


# default state
if not 'xy' in st.session_state:
    st.session_state["xy"] = get_random_ellipse(center, 100)

if not 'drawing' in st.session_state:
    st.session_state["drawing"] = True

# sample ellipse
img  = Image.new("RGB", (width, height), "#ffffff")
img1 = ImageDraw.Draw(img)
img1.polygon(st.session_state["xy"], fill ="#ffffff", outline ="blue")
st.image(img)

if st.session_state["drawing"]:
    st.session_state["st_canvas_result"] = st_canvas(
        #fill_color="rgba(255, 165, 0, 0.3)",  # Fixed fill color with some opacity
        stroke_width=stroke_width,
        stroke_color=stroke_color,
        background_color=bg_color,
        #background_image=Image.open(bg_image) if bg_image else None,
        update_streamlit=True,
        height=height,
        width=width,
        drawing_mode="freedraw",
        #point_display_radius=point_display_radius if drawing_mode == 'point' else 0,
        key="canvas",
    )
else:
    # Do something interesting with the image data and paths
    # if canvas_result.image_data is not None:
    #     st.image(canvas_result.image_data)

    canvas_result = st.session_state["st_canvas_result"]
    objects = pd.json_normalize(canvas_result.json_data["objects"])

    if not objects.empty:

        # preparing the drawing area
        res_img  = Image.new("RGB", (width, height), "#ffffff")
        img1 = ImageDraw.Draw(res_img)

        # getting the coordinates from the drawing path
        x = objects.path.tail(1).values[0]

        tmp = pd.DataFrame(x, columns=['type', 'x0', 'y0', 'x1', 'y1'])
        tmp = tmp[tmp.type == 'Q']

        a = tmp[['x0', 'y0']]
        b = tmp[['x1', 'y1']]

        a.columns = ['x', 'y']
        b.columns = ['x', 'y']

        drawing_coordinates = pd.concat([a, b], ignore_index=True)

        # calculate the best ellipse
        best_ellipse_parms = get_best_ellipse_alt(drawing_coordinates)
        best_ellipse = get_ellipse(
            center,
            best_ellipse_parms['major'],
            best_ellipse_parms['ratio'],
            best_ellipse_parms['rotation'], 100)


        # best ellipse drawing (red)
        img1.polygon(best_ellipse, outline ="red")

        # target ellipse
        img1.polygon(st.session_state["xy"], outline ="blue")

        # actual drawn ellipse
        tmp = best_ellipse_parms['center']
        xy = [tuple(x) for x in drawing_coordinates.to_records(index=False)]
        xy = [(x - tmp[0] + center[0], y - tmp[1] + center[1]) for x, y in xy]
        img1.polygon(xy, outline ="black")


        st.image(res_img)