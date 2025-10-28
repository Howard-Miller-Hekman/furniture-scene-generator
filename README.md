# furniture-scene-generator

This project generates photorealistic room scenes for furniture products by combining product image analysis with image-generation and editing models. 

## Features

It integrates Google Vertex AI (Imagen / Gemini family), Google Cloud Vision for image analysis, and optional SFTP upload for produced assets. The repository includes a runnable script and a small Python package providing services, prompt/LLM orchestration, and data schemas.

- Analyze product silo images to detect furniture type, style, material, and dominant color (Google Cloud Vision).
- Create detailed, product-aware prompts for image generation and editing.
- Use a workflow agent (graph-based) to improve prompts, load and resize source images, and invoke image-capable chat models for editing/generation.
- Generate room-scene images via Google Vertex AI image generation model and save them to local output files.
- Upload generated images to an SFTP server and return a public URL.
- Read and update an Excel spreadsheet of products, writing generated lifestyle image URLs back to the sheet.

## Requirements

- Python 3.8+ (project uses TypedDict, pydantic and newer libraries—verify compatibility with your environment)
- Google Cloud project with Vertex AI and Vision API access
- Credentials JSON for Google Cloud service account with appropriate permissions
- An Excel file matching expected column names (see Usage)
- Network access for external image URLs and Vertex AI

The repository includes a `Pipfile` to install dependencies via Pipenv. Alternately install packages using pip (see Installation).

## Configuration

The runtime reads configuration from environment variables. Important variables used by the project (defaults shown when applicable):

- `GOOGLE_PROJECT_ID` — Google Cloud project id (required)
- `GOOGLE_LOCATION` — Vertex AI location (default: `us-central1`)
- `GOOGLE_CREDENTIALS_PATH` — Path to service account JSON credentials used by Google libraries
- `EXCEL_INPUT_PATH` — Path to input Excel file (default set in `furniture_scene_generator.config.EXCEL_INPUT_PATH`)
- `EXCEL_OUTPUT_PATH` — Path to write updated Excel file (default set in `furniture_scene_generator.config.EXCEL_OUTPUT_PATH`)
- `SFTP_HOST`, `SFTP_PORT`, `SFTP_USERNAME`, `SFTP_PASSWORD`, `SFTP_REMOTE_PATH`, `SFTP_BASE_URL` — SFTP connection and public URL settings for uploading generated images

Set these variables in your shell (example for PowerShell):

```powershell
$env:GOOGLE_PROJECT_ID = "your-project-id"
$env:GOOGLE_CREDENTIALS_PATH = "C:\path\to\credentials.json"
$env:EXCEL_INPUT_PATH = "C:\path\to\input.xlsx"
$env:SFTP_HOST = "sftp.example.com"
# and so on for other SFTP vars
```

## Installation

Using Pipenv (preferred if you have it):

```powershell
# from repository root
pipenv install --dev
pipenv shell
```

Using virtualenv + pip:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install pipenv
pipenv install --dev
# or install needed packages directly with pip using the Pipfile for reference
```

Note: The project uses Google Vertex AI and google-cloud-vision. Ensure the `GOOGLE_CREDENTIALS_PATH` file exists and the account has appropriate Vertex AI and Vision API permissions.

## Usage

Primary runnable script: `furniture_scene_python.py` (in the repository root). This script processes the Excel input file row-by-row and attempts to generate a lifestyle/room scene image for each product, then writes the resulting public image URL back into the Excel file.

Basic run (PowerShell):

```powershell
# with required env vars set
python furniture_scene_python.py
```

Behavior summary:
- The script creates `./output` if needed and writes generated images there.
- It reads the Excel file configured by `EXCEL_INPUT_PATH` (default in `furniture_scene_generator.config`).
- Required columns in the Excel input: `WL`, `Silo Image`, `Lifestyle Image`. Other columns such as `Model`, `QOH`, `Retail`, `MAP`, `Cost`, `Landed Cost`, `WebSite Link for Context`, `comment`, and `Edited Image` are read when present.
- If a row already has a `Lifestyle Image` value, the script skips that row.

Module-level usage

Key modules and functions provided by the package `furniture_scene_generator`:

- `services.py` — utility functions for:
	- initializing Google clients: `initialize_google_clients()`
	- downloading and encoding images: `download_image`, `get_image_url_data`, `url_to_data_url`
	- image processing: `pad_image_to_size`, `downscale_image`, `pad_and_resize_image`, `get_image_dimensions`
	- create prompt helper: `create_place_image_in_room_prompt()`
	- generate image via Vertex AI: `generate_room_scene(imagen_model, prompt, output_path)`
	- upload to SFTP: `upload_to_sftp(local_path, remote_filename)`
	- read/convert spreadsheet rows: `read_excel_file()`, `row_to_product_data()`
	- orchestrator: `generate_room_scene_with_agent(agent, original_prompt, product_data, local_output_path)`

- `llm.py` — chat and image-capable model wrappers and a small state-graph workflow:
	- `create_chat_model()` / `create_image_chat_model()` — initialize language models (configured for Google Vertex AI)
	- `create_agent()` — returns a compiled workflow that runs nodes: improve_prompt → load_image → resize_image → edit_image

- `schema.py` — Pydantic `ProductData` model (fields: model, qoh, wl, retail, MAP, cost, landed_cost, silo_image, website_link_for_context, lifestyle_image, comment, edited_image) and `ImageEditState` typed dictionary used by the agent workflow.

Example: using the packaged agent to edit or generate images (conceptual)

```python
from furniture_scene_generator import llm, services, config

vision_client, imagen_model = services.initialize_google_clients()
agent = llm.create_agent()

# construct product_data via services.row_to_product_data(row)
# prompt = services.create_place_image_in_room_prompt()
# services.generate_room_scene_with_agent(agent, prompt, product_data, './output/my_product_room.png')
```

## Input/Output

- Input: Excel file with product rows (see required columns above). Product silo images are expected to be accessible URLs.
- Output: Generated image files saved under `./output` and an updated Excel file written to the location given by `EXCEL_OUTPUT_PATH`.

## Environment variables and file locations

Configuration defaults and values are defined in `furniture_scene_generator.config`. Environment variables override these defaults. Verify `GOOGLE_CREDENTIALS_PATH` and `EXCEL_INPUT_PATH` before running.

## Troubleshooting notes

- If the script fails to initialize Google clients, confirm `GOOGLE_PROJECT_ID`, `GOOGLE_CREDENTIALS_PATH`, and network access.
- If image generation fails, check Vertex AI quotas, model availability in your project/location, and that the credentials account has Vertex AI permissions.
- SFTP uploads require correct host, credentials and remote path; the code currently disables SFTP host key checking via `pysftp.CnOpts().hostkeys = None` and `cnopts.hostkeys = None`.

## Deployment

Deployment instructions (if present elsewhere in repository) should be preserved. This README does not remove or override existing deployment documentation. See `DOCKER.md`, `docker-compose.yml`, and `Dockerfile*` files in the project root for containerized deployment options and further operational details.

## Project layout

Important files and folders:

- `furniture_scene_python.py` — top-level runnable script that drives processing of the Excel file
- `furniture_scene_generator/` — Python package containing `services.py`, `llm.py`, `schema.py`, `config.py` and `version.py`
- `Pipfile` — dependency specification
- `Dockerfile`, `Dockerfile.cpu`, `docker-compose*.yml`, `DOCKER.md` — container/deployment artifacts (see those files for deployment steps)

## Next steps

- Verify environment variables and Google credentials.
- Prepare an Excel file matching the expected columns and place it where `EXCEL_INPUT_PATH` points.
- Run `python furniture_scene_python.py` and inspect `./output` and the updated Excel file.

If you want, I can also add a minimal example Excel template, or create a small quickstart script that prepares environment variables and demonstrates a single-row run.