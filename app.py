import csv
import json
import os
from pathlib import Path
from typing import Any

import gradio as gr
from dotenv import load_dotenv

from classifier import classify_comments
from scraper import scrape_comments

load_dotenv()

OUTPUT_DIR = Path("outputs")


def _safe_filename(name: str, suffix: str) -> str:
    safe_name = "".join(char for char in name if char.isalnum() or char in (" ", "-", "_")).strip()
    return f"{safe_name or 'youtube_comments'}_comments.{suffix}"


def _write_json_file(title: str, results: list[dict[str, Any]]) -> str:
    OUTPUT_DIR.mkdir(exist_ok=True)
    path = OUTPUT_DIR / _safe_filename(title, "json")
    path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    return str(path)


def _write_csv_file(title: str, results: list[dict[str, Any]]) -> str:
    OUTPUT_DIR.mkdir(exist_ok=True)
    path = OUTPUT_DIR / _safe_filename(title, "csv")

    fieldnames = sorted({key for row in results for key in row.keys()})
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    return str(path)


def process_youtube_video(
    youtube_url: str,
    enable_classification: bool,
    output_format: str,
    progress=gr.Progress(track_tqdm=False),
):
    """
    Scrape YouTube comments, optionally classify them, and export JSON or CSV.
    """
    try:
        if not youtube_url or not youtube_url.strip():
            return None, None, "Error: Please provide a valid YouTube URL"

        api_key = os.getenv("YOUTUBE_API_KEY")
        if not api_key:
            return None, None, "Error: YOUTUBE_API_KEY environment variable not set"

        try:
            progress(0.05, desc="Fetching YouTube comments")
            title, comments = scrape_comments(api_key, youtube_url.strip())
        except ValueError as exc:
            return None, None, f"Error: Invalid YouTube URL - {exc}"
        except Exception as exc:
            return None, None, f"Error scraping comments: {exc}"

        if not comments:
            return None, None, "No comments found for this video"

        if enable_classification:
            try:
                def update_classification_progress(done: int, total: int, message: str) -> None:
                    fraction = 0.15 + (0.75 * done / max(total, 1))
                    progress(fraction, desc=message)

                progress(0.1, desc=f"Preparing {len(comments)} comments for classification")
                results = classify_comments(comments, progress_callback=update_classification_progress)
            except Exception as exc:
                return None, None, f"Error during classification: {exc}"
        else:
            results = comments

        progress(0.92, desc=f"Writing {output_format} output")
        if output_format == "JSON":
            json_path = _write_json_file(title, results)
            progress(1.0, desc="Done")
            return results, json_path, f"Success: Scraped {len(results)} comments from '{title}'. JSON ready."

        if output_format == "CSV":
            csv_path = _write_csv_file(title, results)
            progress(1.0, desc="Done")
            return results, csv_path, f"Success: Scraped {len(results)} comments from '{title}'. CSV ready."

        return None, None, "Error: Invalid output format selected"

    except Exception as exc:
        return None, None, f"Unexpected error: {exc}"


def create_ui():
    """
    Create the Gradio UI.
    """
    with gr.Blocks(title="YouTube Comments Scraper") as app:
        gr.Markdown("# YouTube Comments Scraper + Optional Classifier")
        gr.Markdown("Scrape YouTube comments and optionally classify them into decision-ready categories.")

        with gr.Row():
            with gr.Column():
                url_input = gr.Textbox(
                    label="YouTube Video URL",
                    placeholder="https://www.youtube.com/watch?v=...",
                    lines=1,
                )

                classify_checkbox = gr.Checkbox(
                    label="Enable classification",
                    value=False,
                    info="Classify comments into: Question, Criticism, Affirmation, Other",
                )

                format_dropdown = gr.Dropdown(
                    choices=["JSON", "CSV"],
                    label="Output format",
                    value="JSON",
                )

                run_button = gr.Button("Run", variant="primary")

        with gr.Row():
            with gr.Column():
                json_output = gr.JSON(label="JSON Preview", visible=True)
                file_output = gr.File(label="Download File", visible=True)
                status_output = gr.Textbox(
                    label="Status / Messages",
                    lines=3,
                    interactive=False,
                )

        run_button.click(
            fn=process_youtube_video,
            inputs=[url_input, classify_checkbox, format_dropdown],
            outputs=[json_output, file_output, status_output],
        )

    return app


if __name__ == "__main__":
    app = create_ui()
    app.launch(mcp_server=True, share=False)
