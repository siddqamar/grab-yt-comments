import os
import json
import csv
import io
import gradio as gr
from scraper import scrape_comments
from classifier import classify_comments
from dotenv import load_dotenv

load_dotenv()

def process_youtube_video(
    youtube_url: str,
    enable_classification: bool,
    output_format: str
):
    """
    Main processing function that:
    1. Scrapes YouTube comments
    2. Optionally classifies them
    3. Returns results in selected format
    """
    try:
        # Validate inputs
        if not youtube_url or not youtube_url.strip():
            return None, None, "Error: Please provide a valid YouTube URL"
        
        # Get API key from environment
        api_key = os.getenv("YOUTUBE_API_KEY")
        if not api_key:
            return None, None, "Error: YOUTUBE_API_KEY environment variable not set"
        
        # Step 1: Scrape comments
        try:
            title, comments = scrape_comments(api_key, youtube_url.strip())
        except ValueError as e:
            return None, None, f"Error: Invalid YouTube URL - {str(e)}"
        except Exception as e:
            return None, None, f"Error scraping comments: {str(e)}"
        
        if not comments:
            return None, None, "No comments found for this video"
        
        # Step 2: Optionally classify comments
        if enable_classification:
            try:
                # Pass JSON (list of dicts) to classifier
                classified_df = classify_comments(comments)
                # Convert back to list of dicts with label field
                results = classified_df.to_dict('records')
                # Normalize category names to match spec
                for item in results:
                    category = item.get('category', 'other').lower()
                    if category == 'question':
                        item['label'] = 'Question'
                    elif category == 'criticism':
                        item['label'] = 'Criticism'
                    elif category in ('affirmative', 'affirmation'):
                        item['label'] = 'Affirmation'
                    else:
                        item['label'] = 'Other'
                    # Remove old category field
                    item.pop('category', None)
            except Exception as e:
                return None, None, f"Error during classification: {str(e)}"
        else:
            results = comments
        
        # Step 3: Format output
        if output_format == "JSON":
            json_output = json.dumps(results, indent=2)
            return json_output, None, f"Success: Scraped {len(results)} comments from '{title}'"
        
        elif output_format == "CSV":
            # Convert to CSV
            output = io.StringIO()
            if results:
                fieldnames = list(results[0].keys())
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(results)
            
            csv_content = output.getvalue()
            
            # Create temporary file for download
            filename = f"{title.replace(' ', '_')}_comments.csv"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(csv_content)
            
            return None, filename, f"Success: Scraped {len(results)} comments from '{title}'. CSV ready for download."
        
        else:
            return None, None, "Error: Invalid output format selected"
            
    except Exception as e:
        return None, None, f"Unexpected error: {str(e)}"

def create_ui():
    """
    Create Gradio UI with required components
    """
    with gr.Blocks(title="YouTube Comments Scraper") as app:
        gr.Markdown("# YouTube Comments Scraper + Optional Classifier")
        gr.Markdown("Scrape YouTube comments and optionally classify them into categories.")
        
        with gr.Row():
            with gr.Column():
                url_input = gr.Textbox(
                    label="YouTube Video URL",
                    placeholder="https://www.youtube.com/watch?v=...",
                    lines=1
                )
                
                classify_checkbox = gr.Checkbox(
                    label="Enable classification",
                    value=False,
                    info="Classify comments into: Question, Criticism, Affirmation, Other"
                )
                
                format_dropdown = gr.Dropdown(
                    choices=["JSON", "CSV"],
                    label="Output format",
                    value="JSON"
                )
                
                run_button = gr.Button("Run", variant="primary")
        
        with gr.Row():
            with gr.Column():
                json_output = gr.JSON(
                    label="JSON Preview",
                    visible=True
                )
                
                file_output = gr.File(
                    label="Download CSV",
                    visible=True
                )
                
                status_output = gr.Textbox(
                    label="Status / Messages",
                    lines=3,
                    interactive=False
                )
        
        # Wire up the button
        run_button.click(
            fn=process_youtube_video,
            inputs=[url_input, classify_checkbox, format_dropdown],
            outputs=[json_output, file_output, status_output]
        )
    
    return app

if __name__ == "__main__":
    app = create_ui()
    # Launch with MCP server enabled as per AGENTS.md requirement
    app.launch(mcp_server=True, share=False)
