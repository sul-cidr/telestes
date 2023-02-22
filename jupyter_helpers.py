from ipywidgets import Dropdown, Layout
from IPython.display import HTML, display


def show_video_selector(video_list):
    """
    Selects a video from a list of videos
    """
    select_msg = (
        "<style>.widget-label { min-width: 20ex !important; }</style>"
        "<body><p>Please select the video to explore from the dropdown list.</p></body>"
    )

    display(HTML(select_msg))

    return Dropdown(
        options=[(_["video_name"], _["id"]) for _ in video_list],
        description="Video to explore:",
        disabled=False,
        layout=Layout(width="60%", height="40px"),
    )
