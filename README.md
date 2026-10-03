# AI Video Assistant

Turn a YouTube video or a local audio/video recording into a searchable transcript, concise notes, and a chat grounded in what was said.

The Streamlit interface can analyze a source, then display its title, summary, action items, key decisions, open questions, and transcript. You can search the transcript, ask follow-up questions, choose a visual theme, and download the results as a Markdown report.

## Features

- Analyze a YouTube URL or upload an audio/video file.
- Transcribe English audio locally with Whisper.
- Transcribe Hinglish audio and translate it to English using Sarvam AI.
- Generate a title, summary, action items, decisions, and open questions using Groq.
- Build a local Chroma vector index for transcript-based question answering.
- Search the transcript and download a Markdown report.

## Requirements

- Python 3.10 or newer.
- FFmpeg installed and available on your `PATH`. The Python package `ffmpeg-python` does not install the FFmpeg executable.
- A Groq API key for summaries, extraction, and chat.
- A Sarvam API key when using Hinglish transcription.
- An internet connection for YouTube downloads, API calls, and initial model downloads.

English transcription uses Whisper locally. On the first run, Whisper downloads the selected model, and the embedding model is also downloaded when the vector store is built. These models can require significant disk space and processing time.

## Setup on Windows

Open PowerShell in the project directory and create a virtual environment:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell prevents activating the virtual environment, run the Python executable directly instead:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Install FFmpeg separately and confirm that `ffmpeg` is available from a new terminal:

```powershell
ffmpeg -version
```

## Configure API keys

Create a `.env` file in the project root:

```dotenv
GROQ_API_KEY=your_groq_api_key
SARVAM_API_KEY=your_sarvam_api_key
```

`GROQ_API_KEY` is used for the LLM features. `SARVAM_API_KEY` is only required when selecting Hinglish. Keep `.env` private; it is excluded from Git.

Optional transcription settings:

```dotenv
WHISPER_MODEL=small
SARVAM_STT_MODEL=saaras:v4
```

`WHISPER_MODEL` defaults to `small`. Whisper offers model sizes such as `tiny`, `base`, `small`, `medium`, and `large`; larger models typically need more memory and take longer to run.

## Run the Streamlit app

From the project root, with the virtual environment active:

```powershell
streamlit run app.py
```

Streamlit prints a local URL (usually `http://localhost:8501`) to open in your browser. Choose a YouTube URL or upload a supported audio/video file, select English or Hinglish, then select **Analyze video**.

Supported upload extensions in the UI: `mp3`, `wav`, `m4a`, `mp4`, `mkv`, `mov`, and `webm`.

## Run the command-line interface

The project also includes a command-line workflow:

```powershell
python main.py
```

Enter a YouTube URL or a local file path, choose a language, and then ask questions in the terminal.

## Project layout

```text
.
├── app.py                   # Streamlit user interface and workflow
├── main.py                  # Command-line workflow
├── core/
│   ├── extractor.py         # Action items, decisions, and open questions
│   ├── rag_engine.py        # Retrieval-augmented transcript chat
│   ├── summarizer.py        # Title and summary generation
│   ├── transcriber.py       # Whisper and Sarvam transcription
│   └── vector_store.py      # Embeddings and Chroma vector store
├── utils/
│   └── audio_processor.py   # Downloading, conversion, and audio chunking
├── requirements.txt
├── downloads/               # Generated YouTube audio (created at runtime)
└── vector_db/               # Generated local vector database (created at runtime)
```

`downloads/` and `vector_db/` contain generated data and are intentionally ignored by Git. They can be recreated by running the app again.

## Troubleshooting

- **FFmpeg not found:** Install FFmpeg, add its executable directory to `PATH`, and restart the terminal.
- **Missing API key:** Check that `.env` is in the project root and contains the required key for the selected features.
- **YouTube download or extraction errors:** Check the URL and network access. YouTube may change its extraction requirements; update `yt-dlp` if necessary.
- **Slow first run:** Whisper and the embedding model may need to download before analysis can proceed. CPU transcription can also take a while.
- **Out of memory or slow Whisper transcription:** Set `WHISPER_MODEL` to a smaller model, such as `base` or `tiny`.

## Privacy and data handling

English transcription runs locally through Whisper. Hinglish audio is sent to Sarvam AI for transcription and translation. Transcript analysis and chat questions are sent to Groq. YouTube audio, generated chunks, and the vector database are stored locally while processing. Avoid analyzing recordings unless you have permission to use them with the selected services.
