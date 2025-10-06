import os
import requests
import mimetypes
import base64
import logging
from decimal import Decimal

import pandas as pd
import pysftp
from google.cloud import vision
from vertexai.preview.vision_models import ImageGenerationModel
import vertexai

from furniture_scene_generator import config, schema


logger = logging.getLogger(__name__)

def initialize_google_clients():
    """Initialize Google Cloud clients"""
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = config.CREDENTIALS_PATH
    
    # Initialize Vertex AI
    vertexai.init(project=config.PROJECT_ID, location=config.LOCATION)
    
    # Initialize Vision client
    vision_client = vision.ImageAnnotatorClient()
    
    # Initialize Imagen model
    imagen_model = ImageGenerationModel.from_pretrained("imagegeneration@006")
    
    return vision_client, imagen_model


def download_image(url):
    """Download an image from URL"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.content
    except Exception as e:
        raise Exception(f"Failed to download image: {str(e)}")


def analyze_product_image(vision_client, image_url, website_url=''):
    """Analyze product image to determine furniture type, style, and characteristics"""
    print(f"  → Analyzing image from URL...")
    
    try:
        # Download the image
        image_content = download_image(image_url)
        
        # Prepare image for Vision API
        image = vision.Image(content=image_content)
        
        # Perform analysis
        features = [
            vision.Feature(type_=vision.Feature.Type.LABEL_DETECTION, max_results=15),
            vision.Feature(type_=vision.Feature.Type.IMAGE_PROPERTIES),
            vision.Feature(type_=vision.Feature.Type.OBJECT_LOCALIZATION),
            vision.Feature(type_=vision.Feature.Type.WEB_DETECTION)
        ]
        
        request = vision.AnnotateImageRequest(image=image, features=features)
        response = vision_client.annotate_image(request=request)
        
        # Extract analysis results
        labels = [label.description.lower() for label in response.label_annotations]
        objects = [obj.name.lower() for obj in response.localized_object_annotations]
        web_entities = [entity.description.lower() for entity in response.web_detection.web_entities if entity.description]
        
        # Extract hints from website URL
        url_hints = []
        if website_url:
            url_hints = website_url.lower().replace('-', ' ').replace('/', ' ').split()
        
        all_hints = labels + objects + web_entities + url_hints
        
        # Determine furniture type
        furniture_type, sub_type = detect_furniture_type(all_hints)
        
        # Determine style
        style = detect_style(all_hints)
        
        # Determine material
        material = detect_material(all_hints)
        
        # Get dominant color
        color_desc = 'medium wood'
        if response.image_properties_annotation.dominant_colors.colors:
            color = response.image_properties_annotation.dominant_colors.colors[0].color
            color_desc = determine_color_description(color.red, color.green, color.blue)
        
        print(f"  ✓ Detected: {furniture_type}{' (' + sub_type + ')' if sub_type else ''}, Style: {style}, Color: {color_desc}")
        
        return {
            'furniture_type': furniture_type,
            'sub_type': sub_type,
            'style': style,
            'material': material,
            'color_desc': color_desc,
            'labels': labels
        }
        
    except Exception as e:
        print(f"  ✗ Error analyzing image: {str(e)}")
        raise


def detect_furniture_type(hints):
    """Detect furniture type from hints"""
    furniture_type = 'furniture piece'
    sub_type = ''
    
    # Check for clocks
    if any('clock' in h for h in hints):
        if any(h in hints for h in ['grandfather', 'floor']):
            furniture_type = 'grandfather clock'
            sub_type = 'floor clock'
        elif 'wall' in hints:
            furniture_type = 'wall clock'
        elif any(h in hints for h in ['mantel', 'mantle']):
            furniture_type = 'mantel clock'
        elif 'table' in hints:
            furniture_type = 'table clock'
        else:
            furniture_type = 'clock'
    
    # Check for curio cabinets
    elif 'curio' in hints:
        furniture_type = 'curio cabinet'
        sub_type = 'display cabinet'
    
    # Check for wine/bar cabinets
    elif any('wine' in h and any(x in h for x in ['bar', 'cabinet', 'rack']) for h in hints):
        furniture_type = 'wine cabinet'
        sub_type = 'wine bar'
    elif any('bar' in h and ('cabinet' in h or 'cart' in h) for h in hints):
        furniture_type = 'bar cabinet'
        if 'cart' in hints:
            sub_type = 'bar cart'
    
    # Check for other cabinet types
    elif 'console' in hints:
        furniture_type = 'console cabinet'
    elif any('display' in h and 'cabinet' in h for h in hints):
        furniture_type = 'display cabinet'
    elif 'cabinet' in hints:
        furniture_type = 'cabinet'
    
    # Check for other furniture
    elif any(h in hints for h in ['bookcase', 'bookshelf']):
        furniture_type = 'bookcase'
    elif 'chest' in hints:
        furniture_type = 'chest'
    
    return furniture_type, sub_type


def detect_style(hints):
    """Detect style from hints"""
    if any(h in hints for h in ['modern', 'contemporary']):
        return 'modern'
    elif any(h in hints for h in ['rustic', 'farmhouse']):
        return 'rustic'
    elif 'industrial' in hints:
        return 'industrial'
    elif 'transitional' in hints:
        return 'transitional'
    elif any(h in hints for h in ['vintage', 'antique']):
        return 'vintage'
    elif any(h in hints for h in ['elegant', 'formal']):
        return 'elegant traditional'
    elif any(h in hints for h in ['traditional', 'classic']):
        return 'traditional'
    else:
        return 'traditional'


def detect_material(hints):
    """Detect material from hints"""
    if 'cherry' in hints:
        return 'cherry wood'
    elif 'oak' in hints:
        return 'oak wood'
    elif 'mahogany' in hints:
        return 'mahogany wood'
    elif 'walnut' in hints:
        return 'walnut wood'
    elif any(h in hints for h in ['wood', 'wooden']):
        return 'wood'
    elif 'metal' in hints:
        return 'metal and wood'
    elif 'glass' in hints:
        return 'wood with glass'
    else:
        return 'wood'


def determine_color_description(r, g, b):
    """Determine color description from RGB values"""
    if r < 50 and g < 50 and b < 50:
        return 'dark'
    elif r > 200 and g > 200 and b > 200:
        return 'light'
    elif r > 150 and g < 100 and b < 100:
        return 'warm wood'
    elif r > 100 and g > 80 and b < 70:
        return 'rich wood'
    else:
        return 'medium wood'


def generate_room_scene_prompt(wl_model, analysis):
    """Generate a detailed prompt for room scene creation"""
    furniture_type = analysis['furniture_type']
    sub_type = analysis['sub_type']
    style = analysis['style']
    material = analysis['material']
    color_desc = analysis['color_desc']
    
    # Determine room context based on furniture type
    room_type, room_desc, placement, context = get_room_context(furniture_type)
    
    # Create detailed prompt
    prompt = f"""Create a photorealistic, high-end interior design photograph featuring a {color_desc} {material} {furniture_type}{' / ' + sub_type if sub_type else ''} in a {room_desc}. 

THE {furniture_type.upper()} MUST BE:
- The absolute focal point and hero of the image
- {placement}
- Fully visible from a flattering 3/4 front angle with no obstructions
- Crystal clear, sharp focus showing all intricate details
- Well-lit with professional lighting that highlights its craftsmanship
- Taking up significant visual space in the composition (prominent but not cropped)

ROOM STYLING:
- {style.capitalize()} interior design aesthetic
- {context}
- Multiple light sources: natural window light, subtle accent lighting, warm ambient fixtures
- Professional styling with attention to balance and negative space
- Clean, uncluttered composition that draws the eye directly to the {furniture_type}

PHOTOGRAPHY QUALITY:
- Professional interior design photography for luxury furniture catalogs
- Architectural Digest or Elle Decor editorial quality
- 8K ultra-high resolution with exceptional clarity
- Perfect exposure, color accuracy, and white balance
- Natural depth of field with slight background softness to emphasize the main piece
- Shot with professional camera and wide-angle lens

COLOR PALETTE: Rich, harmonious colors that complement the {color_desc} tones of the {furniture_type}, creating an aspirational yet attainable space that makes the furniture piece irresistible."""
    
    print(f"  → Generated prompt for {style} {room_type} scene")
    return prompt


def get_room_context(furniture_type):
    """Get appropriate room context for furniture type"""
    import random
    
    if 'wine' in furniture_type or 'bar' in furniture_type:
        options = [
            ('dining room', 'sophisticated dining room with elegant table setting visible in background',
             'positioned along the wall as a statement piece',
             'fine dining table with chairs, elegant chandelier overhead'),
            ('living room', 'upscale living room with comfortable seating area',
             'featured prominently near the seating area',
             'plush sofa, armchairs, coffee table with books'),
            ('home entertainment area', 'dedicated home bar or entertainment space',
             'as the centerpiece of the entertainment area',
             'bar stools, ambient lighting, tasteful wall art')
        ]
        return random.choice(options)
    
    elif 'curio' in furniture_type or 'display' in furniture_type:
        options = [
            ('living room', 'elegant living room with refined furnishings',
             'displayed prominently as a focal point',
             'comfortable seating, side tables, decorative accessories visible inside the cabinet'),
            ('dining room', 'formal dining room with sophisticated ambiance',
             'featured elegantly against the wall',
             'dining table in background, fine china or collectibles visible inside the cabinet'),
            ('entryway or foyer', 'grand entryway with welcoming atmosphere',
             'showcased as a statement piece',
             'elegant mirror, console table, decorative items displayed inside the cabinet')
        ]
        return random.choice(options)
    
    elif 'grandfather' in furniture_type or 'floor' in furniture_type:
        options = [
            ('living room', 'classic living room with timeless elegance',
             'standing majestically as a centerpiece',
             'traditional furniture, area rug, the clock commanding attention'),
            ('entryway or foyer', 'grand entryway with welcoming presence',
             'positioned impressively to greet visitors',
             'elegant console table, mirror, the clock as a statement piece'),
            ('home library or study', 'distinguished library or study with rich character',
             'standing prominently in a corner or along the wall',
             'bookshelves, leather furniture, warm wood tones')
        ]
        return random.choice(options)
    
    elif 'wall' in furniture_type and 'clock' in furniture_type:
        return ('living room or dining room', 'well-appointed room with classic style',
                'mounted prominently on the wall at eye level',
                'complementary furniture below, balanced room composition')
    
    elif 'mantel' in furniture_type:
        return ('living room', 'cozy living room with fireplace',
                'displayed elegantly on the fireplace mantel',
                'comfortable seating, fireplace, the clock as a mantel centerpiece')
    
    elif 'clock' in furniture_type:
        return ('living room or study', 'refined interior space',
                'positioned prominently on a side table or shelf',
                'tasteful furniture, the clock clearly visible')
    
    else:
        return ('living room or dining room', 'beautifully appointed room with elegant furnishings',
                'positioned prominently as a featured piece',
                'complementary furniture and sophisticated decor')


def generate_room_scene(imagen_model, prompt, output_path):
    """Generate room scene image using Imagen API"""
    print(f"  → Generating room scene with Imagen API...")
    
    try:
        # Generate image
        response = imagen_model.generate_images(
            prompt=prompt,
            number_of_images=1,
            aspect_ratio="16:9",
            safety_filter_level="block_some",
            person_generation="dont_allow"
        )
        
        if not response or not response.images:
            raise Exception("No images generated by Imagen API")
        
        # Save the image
        image = response.images[0]
        image._pil_image.save(output_path)
        
        print(f"  ✓ Image saved to: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"  ✗ Error generating image: {str(e)}")
        raise


def upload_to_sftp(local_path, remote_filename):
    """Upload image to SFTP server"""
    print(f"  → Uploading to SFTP server...")
    
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None  # Disable host key checking (use with caution)
    
    try:
        with pysftp.Connection(
            host=config.SFTP_HOST,
            port=config.SFTP_PORT,
            username=config.SFTP_USERNAME,
            password=config.SFTP_PASSWORD,
            cnopts=cnopts
        ) as sftp:
            remote_path = os.path.join(config.SFTP_REMOTE_PATH, remote_filename).replace('\\', '/')
            sftp.put(local_path, remote_path)
            
            public_url = f"{config.SFTP_BASE_URL.rstrip('/')}/{remote_filename}"
            print(f"  ✓ Uploaded successfully: {public_url}")
            return public_url
            
    except Exception as e:
        print(f"  ✗ SFTP upload error: {str(e)}")
        raise



def create_place_image_in_room_prompt(room_type="living room", other_possible_furniture="sofa and chairs") -> str:
    return (
        "Analyze the attached photo of a piece of furniture to determine "
        "its style. Then, generate a high-resolution, photorealistic image "
        f"of a {room_type} scene that is aesthetically appropriate for that "
        "furniture style, placing the furniture item within it. The "
        "furniture should be clearly visible, so position other furnishings "
        f"(like the {other_possible_furniture}) to the sides or background to ensure "
        "the main item is the focal point."
    )


def url_to_data_url(url: str) -> str:
    # If it's already a data URL, return as-is
    if url.strip().lower().startswith("data:"):
        return url

    # Guess the MIME type from the URL
    mime_type, _ = mimetypes.guess_type(url)

    if mime_type and mime_type.startswith("image/"):
        try:
            # Download the image
            response = requests.get(url)
            response.raise_for_status()

            # Encode the image content as base64
            encoded = base64.b64encode(response.content).decode("utf-8")

            # Build data URL
            data_url = f"data:{mime_type};base64,{encoded}"
            return data_url
        except Exception as e:
            # If anything goes wrong, fallback to original URL
            print(f"Error downloading/encoding image: {e}")
            return url
    else:
        # Not an image → return original URL
        return url


def image_url_to_message(url: str):
    normal_image_url = url_to_data_url(url)
    return {
        "type": "image_url",
        "image_url": { "url": normal_image_url}
    }


def read_excel_file():
    # Read Excel file
    logger.info(f"\n📂 Reading Excel file: {config.EXCEL_INPUT_PATH}")
    df = pd.read_excel(config.EXCEL_INPUT_PATH)
    logger.info(f"✓ Found {len(df)} products")    
    return df



def row_to_product_data(row) -> schema.ProductData:
    row_dict = row.to_dict()
    
    # Create ProductData object from row
    # Map DataFrame columns to schema fields
    # Pydantic will handle type validation and conversion
    product_data = schema.ProductData(
        model=str(row_dict.get('Model', '')),
        qoh=int(row_dict['QOH']) if pd.notna(row_dict.get('QOH')) else None,
        wl=str(row_dict['WL']) if pd.notna(row_dict.get('WL')) else None,
        retail=Decimal(str(row_dict['Retail'])) if pd.notna(row_dict.get('Retail')) else None,
        MAP=Decimal(str(row_dict['MAP'])) if pd.notna(row_dict.get('MAP')) else None,
        cost=Decimal(str(row_dict['Cost'])) if pd.notna(row_dict.get('Cost')) else None,
        landed_cost=Decimal(str(row_dict['Landed Cost'])) if pd.notna(row_dict.get('Landed Cost')) else None,
        silo_image=str(row_dict['Silo Image']) if pd.notna(row_dict.get('Silo Image')) else None,
        website_link_for_context=str(row_dict['WebSite Link for Context']) if pd.notna(row_dict.get('WebSite Link for Context')) else None,
        lifestyle_image=str(row_dict['Lifestyle Image']) if pd.notna(row_dict.get('Lifestyle Image')) else None,
    )
    return product_data    


def read_product_data_from_df(df: pd.DataFrame) -> list[schema.ProductData]:
    """Process DataFrame rows and convert to ProductData schema objects."""
    products = []
    
    logger.info(f"\n🔄 Processing {len(df)} products...")
    
    for idx, row in df.iterrows():
        try:
            # Convert row to dictionary and handle NaN values
            product_data = row_to_product_data(row)            
            products.append(product_data)
            logger.debug(f"  ✓ Processed product: {product_data.model}")
            
        except Exception as e:
            logger.error(f"  ✗ Error processing row {idx}: {str(e)}")
            continue
    
    logger.info(f"✓ Successfully processed {len(products)} products")
    return products


def generate_room_scene_with_agent(agent, original_prompt, product_data, local_output_path):
    initial_state = {
        "original_prompt": original_prompt,
        "improved_prompt": "",
        "product_data": product_data,
        "response": None,
        "error": None
    }

    try:
        final_state = agent.invoke(initial_state)
        test_response = final_state['response']
        logger.info("✓ Model is working! Generated test response successfully")
        logger.info(f"  Response type: {type(test_response)}")
        logger.info(f"  Content preview: {str(test_response.content)[:200]}...")
    except Exception as e:
        logging.error(f"Model test failed: {str(e)}", exc_info=True)
        print(f"⚠️ Model test failed: {str(e)}")
        return False

    if test_response:
        for resp in test_response.content:
            if type(resp) == str:
                print(resp)
            elif type(resp) == dict:
                if resp['type'] == 'image_url':
                    image_url = resp['image_url']['url']
                    
                    if image_url.startswith('data:'):
                        # Handle data URL
                        header, encoded = image_url.split(',', 1)
                        image_bytes = base64.b64decode(encoded)
                    else:
                        # Handle remote URL
                        response = requests.get(image_url)
                        response.raise_for_status()
                        image_bytes = response.content

                    with open(local_output_path, 'wb') as f:
                        f.write(image_bytes)
                    return True
            else:
                logger.warning(f"Unknown response type: {type(resp)} : {resp}")

    return False
