# Grab YT Comments: Scrape & Classify with Ease

Ever felt overwhelmed by thousands of comments on a YouTube video? Whether you're a content creator trying to find genuine questions, a founder looking for product feedback, or just a curious soul, **Grab YT Comments** is here to do the heavy lifting for you.

---

## Live Demo
Want to try it out without installing anything? 
**[Click here to visit the live demo on Hugging Face!](https://huggingface.co/spaces/siddqamar/grab-yt-comments)**

---

## Why You’ll Love This

Manual scrolling is a thing of the past. Here is how this tool makes your life easier:

*   **Audience Insights in Seconds:** Instantly see what people are asking or complaining about without reading every single "First!" comment.
*   **Market Research & Feedback:** Perfect for founders and marketers to gather raw, unfiltered feedback from competitors' videos or their own.
*   **Ready-to-Use Data:** Export everything to **CSV** or **JSON**. Feed it into your favorite spreadsheet or another tool for deeper analysis.
*   **Simple & Human:** No complex terminal commands needed once it's running. The clean interface makes it easy for anyone to use.

---

## Project Structure

Here is a quick look at how the magic happens:

```text
grab-yt-comments/
├── app.py              # The heart of the app (UI & main logic)
├── scraper.py          # The engine that talks to YouTube
├── classifier.py       # The brain that categorizes your comments
├── pyproject.toml      # Project dependencies for uv
├── requirements.txt    # Compatibility dependency list for older deploy flows
└── .env                # Your secret vault (for the API key)
```

---

## Getting Started

### 1. Clone the Repository
First, grab the code and move into the project folder:
```bash
git clone https://github.com/siddqamar/grab-yt-comments.git
cd grab-yt-comments
```

### 2. Install uv
This project is set up for [`uv`](https://docs.astral.sh/uv/), which is much faster than plain `pip`.

**On Windows:**
```bash
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**On macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 3. Install Dependencies
From the project folder, run:
```bash
uv sync
```

`uv` will create and manage the local `.venv` automatically.

### 4. Get Your YouTube API Key
To talk to YouTube, you need a "key." It’s free and takes about 2 minutes:
1.  Go to the [Google Cloud Console](https://console.cloud.google.com/).
2.  Create a new project (call it "YT Scraper").
3.  Search for **"YouTube Data API v3"** and click **Enable**.
4.  Go to the **Credentials** tab on the left.
5.  Click **+ Create Credentials** > **API Key**.
6.  Copy that key!

### 5. Setup Your Environment
Create a file named `.env` in the root folder and paste your key there:
```text
YOUTUBE_API_KEY=your_copied_api_key_here
```

### 6. Launch the App
Now, just run:
```bash
uv run python app.py
```
A link will appear in your terminal. Open it in your browser, paste a YouTube URL, and you're good to go!

---

## 💡 Pro Tips
*   **Shorts Work Too!** Just paste the URL of a YouTube Short, and it works exactly the same.
*   **Classification:** If you enable this, the tool uses your local OpenAI-compatible LLM endpoint to classify comments as `appreciation`, `humor`, `questions`, `criticism`, `personal experience`, `feedback`, or `spam`.
*   **Database-backed Results:** The classifier stores the scraped comments first, classifies each saved comment one by one with the LLM, writes labels back to SQLite, and returns the final result from the database.
*   **Classification Timeout:** Tune the LLM request timeout with `CLASSIFICATION_REQUEST_TIMEOUT`.

---

## ⚖️ License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
*Built for creators, researchers, and anyone who values their time.* 🚀
