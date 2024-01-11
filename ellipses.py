import pandas as pd
import numpy as np
from PIL import Image, ImageDraw, ImagePath
import streamlit as st
from streamlit_drawable_canvas import st_canvas
import math
import random
from scipy.optimize import minimize

stroke_color = "#000"
bg_color = "#fff"

width = 800
height = 600

center = (width / 2, height / 2)



def get_ellipse(center, major, ratio, rotation, n_points):
    rotation_radians = rotation / 360 * 2 * math.pi
    rsin, rcos = math.sin(rotation_radians), math.cos(rotation_radians)

    xy = [(math.cos(th)  * major, math.sin(th) * major * ratio )
        for th in [i * (2 * math.pi) / n_points for i in range(n_points)] ]
    xy = [(x * rcos - y * rsin, x * rsin + y * rcos) for x, y in xy]
    xy = [(x + center[0], y + center[1]) for x, y in xy]
    return xy


def get_random_ellipse(center, n_points):

    major = random.uniform(40, 300)
    ratio = random.uniform(.1, 1)
    rotation = random.uniform(0, 360)

    xy = get_ellipse(center, major, ratio, rotation, n_points)
    return xy


def get_best_ellipse(points):

    print(points.head())

    d0 = points.diff().fillna(0) ** 2
    d1 = points.diff(-1).fillna(0) ** 2

    d0 = np.sqrt(d0.x + d0.y)
    d1 = np.sqrt(d1.x + d1.y)

    d = ((d0 + d1) / 2).to_numpy()

    my_points = points.to_numpy()
    my_center = ((my_points[:, 0] * d).sum() / sum(d), (my_points[:, 1] * d).sum() / sum(d))

    print(my_center)

    def error(parms):
        major, ratio, rotation = parms
        xy = get_ellipse(my_center, major, ratio, rotation, len(points))
        xy = np.array(xy)

        #print(my_points[0:5, :])
        #print(xy[0:5, :])

        dists_x = np.subtract.outer(my_points[:, 0], xy[:, 0])
        dists_y = np.subtract.outer(my_points[:, 1], xy[:, 1])
        dists = dists_x**2 + dists_y**2
        out = dists.min(axis=0).sum()
        return out


    out = minimize(error, np.array([300, .5, 45]), method='Nelder-Mead', tol=1e-6)

    #print(out)

    out = {
        'center': my_center,
        'major': out['x'][0],
        'ratio': out['x'][1],
        'rotation': out['x'][2]
    }
    return out


st.sidebar.title("Calculate Button Example")

stroke_width = st.sidebar.slider("Stroke width: ", 1, 25, 3)

if st.sidebar.button("Regenerate ellipse"):
    st.session_state["drawing"] = True
    st.session_state["xy"] = get_random_ellipse(center, 100)

if st.sidebar.button("Calculate"):
    st.session_state["drawing"] = False
    print("hola")


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

        x = objects.path.tail(1).values[0]



        tmp = pd.DataFrame(x, columns=['type', 'x0', 'y0', 'x1', 'y1'])
        tmp = tmp[tmp.type == 'Q']

        a = tmp[['x0', 'y0']]
        b = tmp[['x1', 'y1']]

        a.columns = ['x', 'y']
        b.columns = ['x', 'y']

        drawing_coordinates = pd.concat([a, b], ignore_index=True)

        best_ellipse_parms = get_best_ellipse(drawing_coordinates)

        best_ellipse = get_ellipse(
            center, best_ellipse_parms['major'],
            best_ellipse_parms['ratio'], best_ellipse_parms['rotation'], 100)

        #print(best_ellipse)

        # best ellipse drawing (red)
        res_img  = Image.new("RGB", (width, height), "#ffffff")
        img1 = ImageDraw.Draw(res_img)
        img1.polygon(best_ellipse, outline ="red")

        # target ellipse
        xy = st.session_state["xy"]
        img1.polygon(xy, outline ="blue")

        # actual drawn ellipse
        tmp = [tuple(x) for x in drawing_coordinates.to_records(index=False)]
        tmp = [(x + center[0] - best_ellipse_parms['center'][0], y + center[1] - best_ellipse_parms['center'][1])
            for x, y in tmp
        ]
        img1.polygon(tmp, outline ="black")
        st.image(res_img)

        #st.dataframe(tmp)
