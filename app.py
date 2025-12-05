import os
import traceback
import pandas as pd
import gradio as gr

from scraper import scrape_comments
from classifier import classify_comments  # you already mentioned this exists

# --- basic rate limiting for API fairness ---
MAX_RUNS_PER_DAY = 7
run_count = 0


def core_analyze_youtube_comments(video_url: str, classify: bool = False):
    """
    Core logic shared by BOTH:
      - Gradio UI
      - MCP tool
    Returns a dict that is JSON-serializable.
    """
    global run_count

    api_key = os.getenv("YOUTUBE_API_KEY")

    if not api_key:
        return {
            "status": "error",
            "message": "missing youtube api key — set `YOUTUBE_API_KEY` in your Space secrets",
            "title": None,
            "comment_count": 0,
            "comments": [],
            "csv_path": None,
        }

    if run_count >= MAX_RUNS_PER_DAY:
        return {
            "status": "error",
            "message": "you've reached today's usage limit (7 runs). please come back tomorrow 💫",
            "title": None,
            "comment_count": 0,
            "comments": [],
            "csv_path": None,
        }

    try:
        # uses your scraper.py
        title, comments = scrape_comments(api_key, video_url)
        df = pd.DataFrame(comments)

        # optional classification
        if classify:
            # this assumes classify_comments returns a DataFrame aligned with the texts
            classified_df = classify_comments(df["text"].to_list())
            # if it returns a DataFrame, use that; if it returns list[dict], adjust accordingly
            df = pd.DataFrame(classified_df)

        # CSV for the UI download
        safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "-", "_")).rstrip()
        csv_path = f"{safe_title or 'youtube_comments'}.csv"
        df.to_csv(csv_path, index=False)

        run_count += 1

        return {
            "status": "ok",
            "message": f"successfully fetched {len(df)} comments from **{title}**",
            "title": title,
            "comment_count": len(df),
            "comments": df.to_dict(orient="records"),  # <-- this is what ChatGPT will actually use
            "csv_path": csv_path,
        }

    except Exception as e:
        err = str(e).lower()
        if "quota" in err or "403" in err or "429" in err:
            msg = "sadly, the youtube api quota for the day is used up. please come back tomorrow 💫"
        else:
            msg = f"something went wrong: {e}"

        traceback.print_exc()

        return {
            "status": "error",
            "message": msg,
            "title": None,
            "comment_count": 0,
            "comments": [],
            "csv_path": None,
        }


# --- Gradio-facing function (what the button calls) ---
def analyze_youtube_comments_ui(video_url: str, classify: bool):
    """
    This is ONLY for the Gradio UI.
    It maps the core dict -> (status markdown, file path).
    """
    result = core_analyze_youtube_comments(video_url, classify)
    status_md = result["message"]
    csv_path = result["csv_path"]
    return status_md, csv_path


# --- Gradio UI definition ---
with gr.Blocks(title="youtube comment analyzer") as demo:
    gr.Markdown(
        """
        ## 🎥 youtube comment analyzer  
        paste a youtube video link below and get all comments — or analyze them by tone.
        > each run uses the youtube data api — limited to **7 per day** for fair use.
        """
    )

    with gr.Row():
        video_url = gr.Textbox(
            label="youtube video url",
            placeholder="paste video link here...",
        )
        classify = gr.Checkbox(
            label="classify comments (question / criticism / affirmative)",
            value=False,
        )

    run_btn = gr.Button("fetch comments")
    status = gr.Markdown()
    download = gr.File(label="download csv")

    # connect UI -> core
    run_btn.click(
        fn=analyze_youtube_comments_ui,
        inputs=[video_url, classify],
        outputs=[status, download],
    )


# --- MCP Tool Definition ---
# Define the MCP tool as a simple function that Gradio will expose
def analyze_youtube_comments(video_url: str, classify: bool = False):
    """
    Fetch and analyze YouTube comments from a video URL.
    
    Args:
        video_url: The YouTube video URL to scrape comments from
        classify: Whether to classify comments by tone (question/criticism/affirmative)
    
    Returns:
        A dictionary containing status, message, title, comment_count, and comments list
    """
    result = core_analyze_youtube_comments(video_url, classify)

    # Return JSON-serializable dict without csv_path
    return {
        "status": result["status"],
        "message": result["message"],
        "title": result["title"],
        "comment_count": result["comment_count"],
        "comments": result["comments"],
    }


if __name__ == "__main__":
    # When mcp_server=True, Gradio looks for standalone functions to expose as tools
    # The function 'analyze_youtube_comments' should be automatically discovered
    demo.launch(
        show_error=True, 
        mcp_server=True,
        mcp_functions=[analyze_youtube_comments]  # Explicitly register the MCP function
    )