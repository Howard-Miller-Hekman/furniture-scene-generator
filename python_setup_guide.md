# Python Setup Guide - Furniture Scene Generator
## Step-by-Step Instructions for Non-Developers

---

## 📋 What You'll Need

Before starting, gather:
- [ ] A computer (Windows or Mac)
- [ ] Internet connection
- [ ] Google account (for Google Cloud)
- [ ] Credit card (for Google Cloud - minimal charges)
- [ ] SFTP server credentials
- [ ] Your Excel file: `Overstock White Label Project 093025.xlsx`
- [ ] About 1-2 hours for setup

---

## STEP 1: Install Python

Python 3.8 or higher is required.

### For Windows:

1. Go to: **https://www.python.org/downloads/**
2. Click the big yellow button **"Download Python 3.x.x"**
3. Once downloaded, **run the installer**
4. **IMPORTANT**: Check the box that says **"Add Python to PATH"** at the bottom
5. Click **"Install Now"**
6. Wait for installation to complete
7. Click **"Close"**

### For Mac:

**Option A: Using Python.org (Recommended)**
1. Go to: **https://www.python.org/downloads/**
2. Click **"Download Python 3.x.x"**
3. Open the downloaded `.pkg` file
4. Follow the installation prompts
5. Click through all screens and click **"Install"**

**Option B: Using Homebrew (if you have it)**
1. Open Terminal
2. Type: `brew install python3`
3. Press Enter

### Verify Python Installation:

1. **Windows**: Press Windows key, type `cmd`, press Enter
2. **Mac**: Press Command+Space, type `terminal`, press Enter
3. Type this and press Enter:
   ```bash
   python3 --version
   ```
4. You should see something like: `Python 3.11.5`
5. If you see a version number, you're good!

---

## STEP 2: Install pip (Python Package Manager)

Pip usually comes with Python, but let's verify:

1. In your command prompt/terminal, type:
   ```bash
   pip3 --version
   ```
2. You should see something like: `pip 23.x.x`
3. If you see a version, you're good!
4. If not, type:
   ```bash
   python3 -m ensurepip --upgrade
   ```

---

## STEP 3: Set Up Google Cloud

(This is the same as the Node.js version)

### 3.1: Create Google Cloud Account
1. Go to: **https://console.cloud.google.com**
2. Sign in with your Google account
3. Agree to terms of service

### 3.2: Create a New Project
1. Click **"Select a Project"** at the top
2. Click **"New Project"**
3. Project name: `furniture-scene-generator`
4. Click **"Create"**
5. Wait 30 seconds

### 3.3: Enable Billing
1. Click **"Billing"** in the left menu
2. Click **"Link a Billing Account"**
3. If you don't have one, click **"Create Billing Account"**
4. Enter your credit card
   - Cost: ~$0.02-$0.04 per image
   - Total for 63 images: ~$1.26-$2.52

### 3.4: Enable Required APIs
1. In the search bar, type: `Vertex AI API`
2. Click on **"Vertex AI API"**
3. Click **"Enable"**
4. Wait 1-2 minutes

Now search for and enable:
5. Search: `Cloud Vision API`
6. Click **"Enable"**

### 3.5: Create Service Account
1. Go to **"IAM & Admin"** → **"Service Accounts"**
2. Click **"+ Create Service Account"**
3. Name: `furniture-scene-generator`
4. Click **"Create and Continue"**
5. Role: Select **"Vertex AI User"**
6. Click **"Continue"**
7. Also add role: **"Cloud Vision AI Service Agent"**
8. Click **"Continue"** → **"Done"**

### 3.6: Download Credentials
1. Click on your service account email
2. Go to **"Keys"** tab
3. Click **"Add Key"** → **"Create new key"**
4. Select **"JSON"**
5. Click **"Create"**
6. File downloads automatically
7. **Rename it to**: `google-credentials.json`

### 3.7: Note Your Project ID
1. Go back to Cloud Console home
2. Copy your **Project ID** (looks like `furniture-scene-generator-123456`)
3. **Write this down!**

---

## STEP 4: Create Your Project Folder

### 4.1: Create Main Folder
1. Open File Explorer (Windows) or Finder (Mac)
2. Go to your **Documents** folder
3. Create a new folder: `furniture-scene-generator`

### 4.2: Create Subfolders
Inside `furniture-scene-generator`, create:
- `credentials`
- `input`
- `output`

### 4.3: Move Files
1. Move `google-credentials.json` into the `credentials` folder
2. Move `Overstock White Label Project 093025.xlsx` into the `input` folder

Your structure should look like:
```
Documents/
  └── furniture-scene-generator/
      ├── credentials/
      │   └── google-credentials.json
      ├── input/
      │   └── Overstock White Label Project 093025.xlsx
      └── output/
          (empty)
```

---

## STEP 5: Install Python Dependencies

### 5.1: Open Terminal/Command Prompt
**Windows:**
1. Press Windows key
2. Type: `cmd`
3. Press Enter

**Mac:**
1. Press Command + Space
2. Type: `terminal`
3. Press Enter

### 5.2: Navigate to Your Project Folder
Type this (adjust if your folder is elsewhere):

**Windows:**
```bash
cd Documents\furniture-scene-generator
```

**Mac:**
```bash
cd Documents/furniture-scene-generator
```

Press Enter.

### 5.3: Create a Virtual Environment (Recommended)
This keeps your project dependencies isolated:

```bash
python3 -m venv venv
```

Wait for it to complete (takes ~30 seconds).

### 5.4: Activate the Virtual Environment

**Windows:**
```bash
venv\Scripts\activate
```

**Mac/Linux:**
```bash
source venv/bin/activate
```

You should see `(venv)` appear at the start of your command line.

### 5.5: Install Required Packages
Copy and paste this entire command (it's one long line):

```bash
pip install google-cloud-vision google-cloud-aiplatform pandas openpyxl python-dotenv pysftp requests Pillow
```

Press Enter and wait 2-3 minutes. You'll see lots of text as packages install.

When done, you'll see your command prompt again.

---

## STEP 6: Create Configuration Files

### 6.1: Create the .env File

**Windows (Using Notepad):**
1. Open Notepad
2. Copy and paste this:

```
GOOGLE_PROJECT_ID=your-project-id-here
GOOGLE_CREDENTIALS_PATH=./credentials/google-credentials.json
GOOGLE_LOCATION=us-central1

EXCEL_INPUT_PATH=./input/Overstock White Label Project 093025.xlsx
EXCEL_OUTPUT_PATH=./output/Overstock White Label Project 093025_updated.xlsx

SFTP_HOST=ftp.yourwebsite.com
SFTP_PORT=22
SFTP_USERNAME=your-username
SFTP_PASSWORD=your-password
SFTP_REMOTE_PATH=/public_html/furniture-images/
SFTP_BASE_URL=https://yourwebsite.com/furniture-images/
```

3. **Replace these values:**
   - `your-project-id-here` → Your Google Cloud Project ID
   - `ftp.yourwebsite.com` → Your SFTP server address
   - `your-username` → Your SFTP username
   - `your-password` → Your SFTP password
   - `/public_html/furniture-images/` → Your server path
   - `https://yourwebsite.com/furniture-images/` → Your public URL

4. Click **File** → **Save As**
5. Navigate to `furniture-scene-generator` folder
6. File name: `.env` (with the dot!)
7. Save as type: **All Files**
8. Click **Save**

**Mac (Using TextEdit):**
1. Open TextEdit
2. Click **Format** → **Make Plain Text**
3. Copy and paste the configuration above
4. Replace the values (same as Windows)
5. Click **File** → **Save**
6. Navigate to `furniture-scene-generator` folder
7. File name: `.env`
8. Click **Save**

### 6.2: Create the Python Script

**Windows:**
1. Open Notepad
2. Go back to our conversation and find the **"Furniture Scene Generator - Python Version"** artifact
3. Copy ALL the code
4. Paste into Notepad
5. Click **File** → **Save As**
6. Navigate to `furniture-scene-generator` folder
7. File name: `furniture_scene_generator.py`
8. Save as type: **All Files**
9. Click **Save**

**Mac:**
1. Open TextEdit
2. Click **Format** → **Make Plain Text**
3. Copy ALL the code from the Python artifact
4. Paste into TextEdit
5. Click **File** → **Save**
6. Navigate to `furniture-scene-generator` folder
7. File name: `furniture_scene_generator.py`
8. Click **Save**

---

## STEP 7: Verify Your Setup

Your folder should now look like:

```
furniture-scene-generator/
├── credentials/
│   └── google-credentials.json ✓
├── input/
│   └── Overstock White Label Project 093025.xlsx ✓
├── output/
│   (