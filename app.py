import base64
import os
import re
import time
import uuid
from io import BytesIO
from pathlib import Path
import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image
from streamlit_drawable_canvas import st_canvas
from svgpathtools import parse_path
import streamlit.components.v1 as components
from selenium import webdriver
from selenium.webdriver.common.by import By

def main():
    if "button_id" not in st.session_state:
        st.session_state["button_id"] = ""
    if "color_to_label" not in st.session_state:
        st.session_state["color_to_label"] = {}
    PAGES = {
        "Draw": full_app,
    }
    page = st.sidebar.selectbox("Page:", options=list(PAGES.keys()))
    # PAGES[page]()


    components.html(
      """
      <iframe id="frameGrid" width="600" height="400" frameborder="0" scrolling="no" marginheight="0" marginwidth="0" sandbox="allow-forms allow-scripts allow-same-origin" src="https://www.geoportail.gouv.fr/embed/visu.html?c=-5.096703098778556,48.45683452334407&z=18&l0=ORTHOIMAGERY.ORTHOPHOTOS::GEOPORTAIL:OGC:WMTS(1)&permalink=yes" allowfullscreen></iframe>
      """,  width=None, height=700, scrolling=False
    )

    op = webdriver.ChromeOptions()
    op.add_argument('headless')
    driver = webdriver.Chrome()
    frame_grid =  driver.find_element(by=By.ID, value="frameGrid")

    offset_x = frame_grid.rect['x']
    offset_y = frame_grid.rect['y']
    frame_width = frame_grid.rect['width']
    frame_height = frame_grid.rect['height']
  
    st.write(offset_x)
      

def about():
    st.markdown(
        """
    Welcome to the demo of [Streamlit Drawable Canvas](https://github.com/andfanilo/streamlit-drawable-canvas).
    
    On this site, you will find a full use case for this Streamlit component, and answers to some frequently asked questions.
    
    :pencil: [Demo source code](https://github.com/andfanilo/streamlit-drawable-canvas-demo/)    
    """
    )
    st.image("image/demo.jpg")
    st.markdown(
        """
    What you can do with Drawable Canvas:

    * Draw freely, lines, circles and boxes on the canvas, with options on stroke & fill
    * Rotate, skew, scale, move any object of the canvas on demand
    * Select a background color or image to draw on
    * Get image data and every drawn object properties back to Streamlit !
    * Choose to fetch back data in realtime or on demand with a button
    * Undo, Redo or Drop canvas
    * Save canvas data as JSON to reuse for another session
    """
    )


def full_app():
  
    with st.container():
        # Specify canvas parameters in application
        drawing_mode = st.sidebar.selectbox(
            "Drawing tool:",
            ("freedraw", "line", "rect", "circle", "transform", "polygon", "point"),
        )
        stroke_width = st.sidebar.slider("Stroke width: ", 1, 25, 3)
        if drawing_mode == "point":
            point_display_radius = st.sidebar.slider("Point display radius: ", 1, 25, 3)
        stroke_color = st.sidebar.color_picker("Stroke color hex: ")
        bg_image = st.sidebar.file_uploader("Background image:", type=["png", "jpg"])
        realtime_update = st.sidebar.checkbox("Update in realtime", True)

        # Create a canvas component
        # canvas_result = st_canvas(
        #     fill_color = "rgba(255, 165, 0, 0.3)",  # Fixed fill color with some opacity
        #     stroke_width = stroke_width,
        #     stroke_color = stroke_color,
        #     background_image = Image.open(bg_image) if bg_image else None,
        #     update_streamlit = realtime_update,
        #     height = 350,
        #     drawing_mode = drawing_mode,
        #     point_display_radius = point_display_radius if drawing_mode == "point" else 0,
        #     display_toolbar = st.sidebar.checkbox("Display toolbar", True),
        #     key="full_app",
        # )
      

    try:
        Path("tmp/").mkdir()
    except FileExistsError:
        pass

    # Regular deletion of tmp files
    # Hopefully callback makes this better
    now = time.time()
    N_HOURS_BEFORE_DELETION = 1
    for f in Path("tmp/").glob("*.png"):
        st.write(f, os.stat(f).st_mtime, now)
        if os.stat(f).st_mtime < now - N_HOURS_BEFORE_DELETION * 3600:
            Path.unlink(f)

    if st.session_state["button_id"] == "":
        st.session_state["button_id"] = re.sub(
            "\d+", "", str(uuid.uuid4()).replace("-", "")
        )

    button_id = st.session_state["button_id"]
    file_path = f"tmp/{button_id}.png"

    custom_css = f""" 
        <style>
            #{button_id} {{
                display: inline-flex;
                align-items: center;
                justify-content: center;
                background-color: rgb(255, 255, 255);
                color: rgb(38, 39, 48);
                padding: .25rem .75rem;
                position: relative;
                text-decoration: none;
                border-radius: 4px;
                border-width: 1px;
                border-style: solid;
                border-color: rgb(230, 234, 241);
                border-image: initial;
            }} 
            #{button_id}:hover {{
                border-color: rgb(246, 51, 102);
                color: rgb(246, 51, 102);
            }}
            #{button_id}:active {{
                box-shadow: none;
                background-color: rgb(246, 51, 102);
                color: white;
                }}
        </style> """

    data = st_canvas(
            update_streamlit = False,
            fill_color = "rgba(255, 165, 0, 0.3)",  # Fixed fill color with some opacity
            stroke_width = stroke_width,
            stroke_color = stroke_color,
            background_image = Image.open(bg_image) if bg_image else None,
            height = 350,
            drawing_mode = drawing_mode,
            point_display_radius = point_display_radius if drawing_mode == "point" else 0,
            display_toolbar = st.sidebar.checkbox("Display toolbar", True),
            key="c",
        )
    
    if data is not None and data.image_data is not None:
        img_data = data.image_data
        im = Image.fromarray(img_data.astype("uint8"), mode="RGBA")
        im.save(file_path, "PNG")

        buffered = BytesIO()
        im.save(buffered, format="PNG")
        img_data = buffered.getvalue()
        try:
            # some strings <-> bytes conversions necessary here
            b64 = base64.b64encode(img_data.encode()).decode()
        except AttributeError:
            b64 = base64.b64encode(img_data).decode()

        dl_link = (
            custom_css
            + f'<a download="{file_path}" id="{button_id}" href="data:file/txt;base64,{b64}">Export PNG</a><br></br>'
        )
        st.markdown(dl_link, unsafe_allow_html=True)

def print_screen():
    res = pyautogui.locateOnScreen('demo.jpg')


if __name__ == "__main__":
    st.set_page_config(
        page_title="Streamlit Drawable Canvas Demo", page_icon=":pencil2:"
    )
    st.title("Drawable Canvas Demo")
    st.sidebar.subheader("Configuration")
    main()


 

  
