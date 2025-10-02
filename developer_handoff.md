# Technical Specification: Automated Furniture Scene Generation
## Developer Handoff Document

---

## Project Overview

**Objective**: Automate the creation of professional lifestyle/room scene images for furniture products using Google's Imagen 3 AI model.

**Input**: Excel file with 63 furniture products (wine cabinets, curio cabinets, clocks, etc.)

**Output**: 
- AI-generated room scene images featuring each product
- Images uploaded to SFTP server
- Excel file updated with public image URLs

**Tech Stack**: Python 3.8+, Google Cloud Vertex AI (Imagen), Google Cloud Vision API, pandas, pysftp

---

## Business Requirements

### Input Data
- **Source File**: `Overstock White Label Project 093025.xlsx`
- **Key Columns**:
  - Column A: `Model` - Product model number
  - Column C: `WL` - White label model (e.g., "OWP0730") - **used for output filename**
  - Column H: `Silo Image` - Product image URL (clean product shot on white background)
  - Column I: `WebSite Link for Context` - Howard Miller product page URL (optional, for additional context)
  - Column J: `Lifestyle Image` - **OUTPUT: Will be populated with generated image URL**

### Processing Logic
1. Read Excel file
2. For each product row:
   - Skip if `WL` or `Silo Image` is empty
   - Skip if `Lifestyle Image` already has a value (idempotent processing)
   - Download product image from `Silo Image` URL
   - Analyze image using Google Vision API to detect furniture type, style, material, color
   - Optionally parse `WebSite Link for Context` URL for additional product context
   - Generate detailed prompt for room scene based on product characteristics
   - Call Imagen API to generate lifestyle image
   - Save image locally as `{WL}_room.png` (e.g., `OWP0730_room.png`)
   - Upload image to SFTP server
   - Update Excel row with public image URL
3. Save updated Excel file

### Product Type Detection
The script must intelligently detect and handle multiple furniture types:

**Supported Types**:
- Wine cabinets / wine bars
- Bar cabinets / bar carts
- Curio cabinets (display cabinets with glass)
- Grandfather clocks (floor clocks)
- Wall clocks
- Mantel clocks
- Table clocks
- General cabinets, bookcases, chests

**Detection Strategy**:
- Use Google Cloud Vision API label detection, object localization, and web entity detection
- Parse product URL from Column I for keywords (e.g., "wine-bar-cabinet", "grandfather-clock", "curio")
- Combine both sources for accurate classification

### Room Scene Requirements
Each product type should be placed in an appropriate room context:

**Wine/Bar Cabinets**:
- Rooms: Dining room, upscale living room, or home entertainment area
- Context: Table settings, seating areas, bar stools

**Curio Cabinets**:
- Rooms: Elegant living room, formal dining room, grand entryway
- Context: Show decorative items visible inside cabinet, refined furnishings

**Grandfather Clocks**:
- Rooms: Classic living room, grand entryway, home library/study
- Context: Standing majestically as centerpiece, traditional furniture

**Wall Clocks**:
- Rooms: Living room or dining room
- Context: Mounted at eye level with balanced composition

**Mantel Clocks**:
- Rooms: Living room with fireplace
- Context: Displayed on fireplace mantel

### Image Quality Requirements
- **Resolution**: High-quality, suitable for e-commerce (Imagen generates at high resolution)
- **Aspect Ratio**: 16:9 (horizontal/landscape orientation)
- **Product Prominence**: Product must be the focal point, fully visible, well-lit, sharp focus
- **Style**: Professional interior design photography, magazine-quality (Architectural Digest level)
- **Photography**: Multiple light sources, 3/4 front angle, slight depth of field
- **Safety**: No people in images (`person_generation="dont_allow"`)

---

## Technical Implementation

### Architecture
```
┌─────────────────┐
│  Excel Input    │
│  (63 products)  │
└────────┬────────┘
         │
         ↓
┌─────────────────────────────────────┐
│  Python Script                      │
│  ┌───────────────────────────────┐ │
│  │ 1. Read Excel with pandas     │ │
│  └───────────────────────────────┘ │
│  ┌───────────────────────────────┐ │
│  │ 2. Download product image     │ │
│  └───────────────────────────────┘ │
│  ┌───────────────────────────────┐ │
│  │ 3. Analyze with Vision API    │ │
│  │    - Detect furniture type    │ │
│  │    - Detect style/material    │ │
│  │    - Parse URL context        │ │
│  └───────────────────────────────┘ │
│  ┌───────────────────────────────┐ │
│  │ 4. Generate prompt            │ │
│  │    - Room type selection      │ │
│  │    - Style-appropriate desc   │ │
│  └───────────────────────────────┘ │
│  ┌───────────────────────────────┐ │
│  │ 5. Generate image (Imagen)    │ │
│  └───────────────────────────────┘ │
│  ┌───────────────────────────────┐ │
│  │ 6. Upload to SFTP             │ │
│  └───────────────────────────────┘ │
│  ┌───────────────────────────────┐ │
│  │ 7. Update Excel with URL      │ │
│  └───────────────────────────────┘ │
└─────────────────────────────────────┘
         │
         ↓
┌─────────────────┐      ┌──────────────┐
│  Updated Excel  │      │ SFTP Server  │
│  with URLs      │      │ (63 images)  │
└─────────────────┘      └──────────────┘
```

### Dependencies

**Python Packages** (install via pip):
```bash
pip install google-cloud-vision google-cloud-aiplatform pandas openpyxl python-dotenv pysftp requests Pillow
```

**Package Details**:
- `google-cloud-vision` - Vision API for image analysis
- `google-cloud-aiplatform` - Vertex AI for Imagen access
- `pandas` - Excel file manipulation
- `openpyxl` - Excel file reading/writing engine
- `python-dotenv` - Environment variable management
- `pysftp` - SFTP file uploads
- `requests` - HTTP requests for downloading images
- `Pillow` - Image processing

### Google Cloud Setup

**Required GCP Services**:
1. **Vertex AI API** - For Imagen 3 image generation
2. **Cloud Vision API** - For product image analysis

**Authentication**:
- Use Service Account with JSON key file (not API key)
- Required IAM roles:
  - `Vertex AI User`
  - `Cloud Vision AI Service Agent`

**Setup Steps**:
1. Create GCP project
2. Enable billing (required for Vertex AI)
3. Enable Vertex AI API
4. Enable Cloud Vision API
5. Create service account with appropriate roles
6. Download JSON credentials file
7. Set `GOOGLE_APPLICATION_CREDENTIALS` environment variable pointing to JSON file

### Configuration

**Environment Variables** (`.env` file):
```bash
# Google Cloud
GOOGLE_PROJECT_ID=your-gcp-project-id
GOOGLE_CREDENTIALS_PATH=./credentials/google-credentials.json
GOOGLE_LOCATION=us-central1

# File Paths
EXCEL_INPUT_PATH=./input/Overstock White Label Project 093025.xlsx
EXCEL_OUTPUT_PATH=./output/Overstock White Label Project 093025_updated.xlsx

# SFTP Configuration
SFTP_HOST=ftp.example.com
SFTP_PORT=22
SFTP_USERNAME=username
SFTP_PASSWORD=password
SFTP_REMOTE_PATH=/public_html/furniture-images/
SFTP_BASE_URL=https://example.com/furniture-images/
```

**Security Notes**:
- Never commit `.env` or credentials JSON to version control
- Add `.env` and `credentials/` to `.gitignore`
- Consider using Secret Manager for production

### Code Structure

**Main Script**: `furniture_scene_generator.py`

**Key Functions**:

```python
def initialize_google_clients():
    """Initialize Vertex AI and Vision API clients"""
    # Returns: vision_client, imagen_model

def download_image(url):
    """Download image from URL"""
    # Returns: bytes

def analyze_product_image(vision_client, image_url, website_url=''):
    """
    Analyze product image using Vision API
    Detect: furniture_type, sub_type, style, material, color
    Also parse website URL for additional context
    """
    # Returns: dict with analysis results

def detect_furniture_type(hints):
    """Determine furniture type from labels, objects, and URL hints"""
    # Returns: (furniture_type, sub_type)

def detect_style(hints):
    """Determine design style"""
    # Returns: style (traditional, modern, rustic, etc.)

def detect_material(hints):
    """Determine material composition"""
    # Returns: material (wood, cherry wood, metal and wood, etc.)

def generate_room_scene_prompt(wl_model, analysis):
    """
    Generate detailed Imagen prompt based on product analysis
    Includes: room type, style, lighting, composition, quality requirements
    """
    # Returns: prompt string

def get_room_context(furniture_type):
    """
    Select appropriate room setting based on furniture type
    Returns random selection from appropriate options for variety
    """
    # Returns: (room_type, room_description, placement, context)

def generate_room_scene(imagen_model, prompt, output_path):
    """
    Generate image using Imagen API
    Parameters: 16:9 aspect ratio, block_some safety, no people
    """
    # Saves image to output_path

def upload_to_sftp(local_path, remote_filename):
    """Upload image to SFTP server"""
    # Returns: public_url

def main():
    """
    Main processing loop:
    1. Initialize clients
    2. Read Excel
    3. Process each product
    4. Update Excel with results
    5. Print summary statistics
    """
```

### Error Handling

**Strategies**:
- Continue processing on individual product errors (don't fail entire batch)
- Log errors to Excel `Lifestyle Image` column as `ERROR: {message}`
- Track success/skip/error counts
- Print detailed progress for debugging

**Common Issues**:
- Missing/invalid product image URLs → Skip product
- Vision API rate limits → Add delays between requests (2 seconds)
- Imagen API failures → Log error, continue
- SFTP upload failures → Log error, continue
- Network timeouts → Implement retry logic if needed

### Rate Limiting & Performance

**Considerations**:
- Add 2-second delay between products to respect API rate limits
- Process sequentially (not parallel) to control costs and rate limits
- Estimated time: 30-60 seconds per product × 63 = 30-60 minutes total
- Consider batch processing for larger catalogs

**API Quotas** (default):
- Vertex AI Imagen: Check current quotas in GCP Console
- Vision API: 1,800 requests/minute
- May need quota increases for very large batches

### Cost Estimation

**Imagen API Pricing** (as of 2024):
- ~$0.02-$0.04 per image generation
- 63 images = ~$1.26 - $2.52 total

**Vision API Pricing**:
- First 1,000 units/month free
- After: $1.50 per 1,000 units
- 63 image analyses = negligible cost

**Storage/SFTP**:
- Depends on hosting provider
- ~2-5 MB per image × 63 = ~125-315 MB total

---

## Prompt Engineering Strategy

### Prompt Template Structure

Each generated prompt includes:

1. **Product Description**: Type, material, color, style
2. **Product Requirements**: 
   - Must be focal point
   - Specific placement instructions
   - Fully visible, well-lit
   - Sharp focus on details
3. **Room Styling**:
   - Room type and description
   - Style-appropriate elements
   - Lighting specifications
   - Context furniture/decor
4. **Photography Quality**:
   - Professional magazine-quality
   - 8K resolution
   - Proper exposure and color
   - Depth of field specifications
5. **Color Palette**: Harmonious with product

**Example Prompt** (Wine Cabinet):
```
Create a photorealistic, high-end interior design photograph featuring 
a rich wood wood wine cabinet / wine bar in a sophisticated dining room 
with elegant table setting visible in background. 

THE WINE CABINET MUST BE:
- The absolute focal point and hero of the image
- Positioned along the wall as a statement piece
- Fully visible from a flattering 3/4 front angle with no obstructions
- Crystal clear, sharp focus showing all intricate details
- Well-lit with professional lighting that highlights its craftsmanship
- Taking up significant visual space in the composition

ROOM STYLING:
- Traditional interior design aesthetic
- Fine dining table with chairs, elegant chandelier overhead
- Multiple light sources: natural window light, subtle accent lighting
- Professional styling with attention to balance and negative space
- Clean, uncluttered composition

PHOTOGRAPHY QUALITY:
- Professional interior design photography for luxury furniture catalogs
- Architectural Digest or Elle Decor editorial quality
- 8K ultra-high resolution with exceptional clarity
- Perfect exposure, color accuracy, and white balance
- Natural depth of field with slight background softness

COLOR PALETTE: Rich, harmonious colors that complement the rich wood 
tones of the wine cabinet, creating an aspirational yet attainable space.
```

### Room Selection Logic

**Wine/Bar Cabinets** → Random from:
- Sophisticated dining room
- Upscale living room
- Home entertainment area

**Curio Cabinets** → Random from:
- Elegant living room (with collectibles displayed)
- Formal dining room
- Grand entryway

**Grandfather Clocks** → Random from:
- Classic living room
- Grand entryway
- Home library/study

**Other Products** → Context-appropriate rooms

This randomization provides variety across the catalog.

---

## File Naming Convention

**Output Images**: `{WL_MODEL}_room.png`

Examples:
- `OWP0730_room.png`
- `OWP0735_room.png`
- `OWP0709_room.png`

**Rationale**: WL model is unique identifier, consistent format, web-friendly

---

## Testing Strategy

### Development Testing

**Phase 1: Test with 3 products**
```python
# Modify main loop to process only first 3 rows
for idx, row in df.iterrows():
    if idx >= 3:  # Test mode
        break
    # ... rest of processing
```

**Validate**:
- All APIs authenticate correctly
- Images download successfully
- Vision API analysis returns sensible results
- Prompts are well-formed
- Images generate successfully
- SFTP upload works
- Excel updates correctly

**Phase 2: Test product variety**
- Select 1 wine cabinet, 1 curio cabinet, 1 clock
- Verify appropriate room scenes are generated
- Check image quality and product prominence

**Phase 3: Full run**
- Process all 63 products
- Monitor for errors
- Review image quality across all products

### Quality Checks

**For Generated Images**:
- [ ] Product is clearly visible and in focus
- [ ] Product is the main focal point
- [ ] No product truncation/cropping
- [ ] Appropriate room setting for product type
- [ ] Professional lighting and composition
- [ ] High resolution, suitable for e-commerce
- [ ] No people in images
- [ ] Style matches product aesthetic

**For Data**:
- [ ] All 63 rows processed (or skipped with reason)
- [ ] Column J populated with valid URLs
- [ ] URLs are publicly accessible
- [ ] Image files match WL model naming
- [ ] No duplicate images generated

---

## Deployment Considerations

### Production Recommendations

1. **Error Handling**: Add retry logic for transient failures
2. **Logging**: Implement proper logging (not just print statements)
3. **Monitoring**: Track API costs, success rates, processing time
4. **Configuration**: Move to environment-specific configs (dev/staging/prod)
5. **Security**: Use Secret Manager for credentials in production
6. **Scalability**: Consider async processing for large catalogs
7. **Testing**: Add unit tests for key functions
8. **Documentation**: Maintain README with setup instructions

### CI/CD Integration

If automating:
- Docker containerization recommended
- Mount credentials as secrets
- Use cloud storage instead of local filesystem
- Implement webhook triggers for new product additions

### Alternative Approaches

**If Python doesn't work**:
- Node.js version available (same logic, different language)
- Could use Google Cloud Functions for serverless
- Could use Cloud Run for containerized deployment

**Alternative Image Generation**:
- DALL-E 3 via OpenAI API
- Midjourney via API (if available)
- Stable Diffusion (self-hosted or Replicate API)

---

## Troubleshooting Guide

### Common Issues

**"Authentication error"**
- Check `GOOGLE_APPLICATION_CREDENTIALS` path
- Verify JSON credentials file is valid
- Confirm service account has correct IAM roles
- Ensure APIs are enabled

**"API quota exceeded"**
- Check quota limits in GCP Console
- Request quota increase if needed
- Add rate limiting/delays

**"Failed to download image"**
- Verify image URLs in Column H are accessible
- Check network connectivity
- Add timeout handling

**"SFTP connection failed"**
- Verify SFTP credentials
- Test connection with FTP client (FileZilla)
- Check firewall rules
- Verify remote path exists and is writable

**"Image quality issues"**
- Refine prompts for specific product types
- Adjust Imagen parameters
- Try different prompt engineering approaches

**"Wrong furniture type detected"**
- Add more specific keywords to detection logic
- Improve URL parsing
- Add manual overrides if needed

---

## Code Repository Structure

Recommended structure:
```
furniture-scene-generator/
├── .env                          # Environment variables (gitignored)
├── .gitignore                    # Git ignore file
├── README.md                     # Setup instructions
├── requirements.txt              # Python dependencies
├── furniture_scene_generator.py  # Main script
├── credentials/
│   └── google-credentials.json   # GCP credentials (gitignored)
├── input/
│   └── Overstock White Label Project 093025.xlsx
├── output/
│   ├── *.png                     # Generated images
│   └── *.xlsx                    # Updated Excel files
└── tests/
    └── test_furniture_scene.py   # Unit tests (optional)
```

**requirements.txt**:
```
google-cloud-vision==3.4.5
google-cloud-aiplatform==1.38.0
pandas==2.1.3
openpyxl==3.1.2
python-dotenv==1.0.0
pysftp==0.2.9
requests==2.31.0
Pillow==10.1.0
```

**.gitignore**:
```
.env
credentials/
output/*.png
output/*.xlsx
venv/
__pycache__/
*.pyc
.DS_Store
```

---

## Success Criteria

**Definition of Done**:
- [ ] All 63 products processed successfully
- [ ] 63 PNG images generated and uploaded to SFTP
- [ ] Excel file updated with 63 public image URLs
- [ ] All images meet quality standards
- [ ] Script is idempotent (can be re-run safely)
- [ ] Error handling prevents batch failures
- [ ] Documentation complete
- [ ] Costs within budget (<$3 for full run)

---

## Contact & Support

**For Questions**:
- Google Cloud Vertex AI Docs: https://cloud.google.com/vertex-ai/docs
- Google Cloud Vision API Docs: https://cloud.google.com/vision/docs
- Imagen 3 Documentation: https://cloud.google.com/vertex-ai/generative-ai/docs/image/overview

**Script Information**:
- Language: Python 3.8+
- Runtime: ~30-60 minutes for 63 products
- Cost: ~$1.50-$3.00 per full run
- Dependencies: See requirements.txt above

---

## Quick Start Commands

```bash
# 1. Set up virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
# Create .env file with credentials

# 4. Run script
python furniture_scene_generator.py

# 5. Check results
# Review output folder and updated Excel file
```

---

**Document Version**: 1.0
**Last Updated**: 2025-09-30
**Author**: AI Assistant (Claude)
**For**: Furniture Scene Generation Project