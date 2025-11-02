import gradio as gr
import pandas as pd
import traceback
from scraper import scrape_comments
from classifier import classify_comments
import os

MAX_RUNS_PER_DAY = 7
run_count = 0

def analyze_youtube_comments(video_url, classify):
    global run_count
    api_key = os.getenv("YOUTUBE_API_KEY")

    if not api_key:
        return "missing youtube api key — please set it in hugging face secrets as `YOUTUBE_API_KEY`", None

    if run_count >= MAX_RUNS_PER_DAY:
        return "you’ve reached today’s usage limit (7 runs). please come back tomorrow 💫", None

    try:
        title, comments = scrape_comments(api_key, video_url)
        df = pd.DataFrame(comments)
        if classify:
            df = classify_comments(df["text"].to_list())
        csv_path = f"{title}.csv"
        df.to_csv(csv_path, index=False)
        run_count += 1
        return f"successfully fetched {len(df)} comments from **{title}**", csv_path
    except Exception as e:
        err = str(e).lower()
        if "quota" in err or "403" in err or "429" in err:
            return "sadly, the youtube api quota for the day is used up. please come back tomorrow 💫", None
        traceback.print_exc()
        return f"something went wrong: {e}", None

with gr.Blocks(title="youtube comment analyzer") as demo:
    gr.Markdown(
        """
        ## 🎥 youtube comment analyzer  
        paste a youtube video link below and get all comments — or analyze them by tone.
        
        > each run uses the youtube data api — limited to **7 per day** for fair use.
        """
    )
    with gr.Row():
        video_url = gr.Textbox(label="youtube video url", placeholder="paste video link here...")
        classify = gr.Checkbox(label="classify comments (question / criticism / affirmative)", value=False)
    run_btn = gr.Button("fetch comments")
    status = gr.Markdown()
    download = gr.File(label="download csv")

    run_btn.click(analyze_youtube_comments, inputs=[video_url, classify], outputs=[status, download])

if __name__ == "__main__":
    demo.queue(max_size=7).launch(mcp_server=True, show_error=True)
