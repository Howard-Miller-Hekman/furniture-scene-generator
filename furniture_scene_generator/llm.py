from typing import Optional

from furniture_scene_generator import services, schema, config

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
from langchain_core.language_models import BaseChatModel
from langgraph.graph import StateGraph, END


def create_chat_model():
    model = init_chat_model(
        model="gemini-2.5-flash",  # Updated to 2.5
        model_provider="google_vertexai",
        project=config.PROJECT_ID,
        location=config.LOCATION)
    return model


def create_image_chat_model():
    model = init_chat_model(
        model="gemini-2.5-flash-image",  # Updated to 2.5
        model_provider="google_vertexai",
        project=config.PROJECT_ID,
        location=config.LOCATION)
    return model


_chat_model: Optional[BaseChatModel] = None
_image_model: Optional[BaseChatModel] = None


def get_chat_model():
    global _chat_model
    if _chat_model is None:
        _chat_model = create_chat_model()
    return _chat_model


def get_image_model():
    global _image_model
    if _image_model is None:
        _image_model = create_image_chat_model()
    return _image_model


# Define the workflow nodes
def improve_prompt_node(state: schema.ImageEditState) -> schema.ImageEditState:
    """Use chat_model to improve the image editing prompt"""
    print("📝 Improving prompt...")

    # Extract product data for context
    product = state['product_data']

    # Build product context string
    product_context = f"""
Product Information:
- Model: {product.model}
- Retail Price: ${product.retail if product.retail else 'N/A'}
- Style/Category: Based on the product images and context
"""

    if product.website_link_for_context:
        product_context += f"- Product Page: {product.website_link_for_context}\n"

    improvement_message = HumanMessage(
        content=f"""You are an expert at writing image editing prompts for furniture and home decor products.
Improve the following prompt to be more detailed and specific for better image editing results.

{product_context}

Original prompt: {state['original_prompt']}

Instructions:
1. Keep the core intent of placing the furniture in an appropriate room scene
2. Add artistic details about lighting, color harmony, and atmosphere
3. Describe the room style that would best showcase this product
4. Include quality descriptors (photorealistic, high-resolution, professional)
5. Focus on elements that would attract customers to buy this item
6. Consider the price point when describing the room setting
7. Emphasize the furniture as the focal point while creating an aspirational scene

Provide ONLY the improved prompt, nothing else. Do not include any preamble or explanation."""
    )

    try:
        chat_model = get_chat_model()
        response = chat_model.invoke([improvement_message])
        improved = response.content.strip()
        print(f"✓ Improved prompt ({len(improved)} chars)")
        print(f"  Preview: {improved[:150]}...")
        state['improved_prompt'] = improved
    except Exception as e:
        print(f"⚠️ Prompt improvement failed: {str(e)}")
        state['improved_prompt'] = state['original_prompt']
        state['error'] = str(e)

    return state


def edit_image_node(state: schema.ImageEditState) -> schema.ImageEditState:
    """Use image_model to edit the image with the improved prompt"""
    print("🎨 Editing image...")

    image_data = state['source_image_data']
    mime_type = state['source_image_mime_type']

    assert image_data is not None, "Source image data is missing"
    assert mime_type is not None, "Source image MIME type is missing"

    edit_message = HumanMessage([
        state['improved_prompt'],
        services.image_data_to_message(image_data, mime_type)
    ])

    try:
        image_model = get_image_model()
        response = image_model.invoke([edit_message])
        print("✓ Image edited successfully")
        print(f"  Response type: {type(response)}")
        print(f"  Content preview: {str(response.content)[:200]}...")
        state['response'] = response
    except Exception as e:
        print(f"⚠️ Image editing failed: {str(e)}")
        state['error'] = str(e)
        state['response'] = None

    return state


def load_image_node(state: schema.ImageEditState) -> schema.ImageEditState:
    """Load the source image data from the URL"""
    print("📥 Loading source image...")
    try:
        image_data = services.get_image_url_data(
            state['product_data'].silo_image)
        state['source_image_data'] = image_data['image_data']
        state['source_image_mime_type'] = image_data['mime_type']
        print(
            f"✓ Image loaded successfully ({len(image_data['image_data'])} bytes, MIME type: {image_data['mime_type']})")
    except Exception as e:
        print(f"⚠️ Failed to load image: {str(e)}")
        state['error'] = str(e)
        state['source_image_data'] = None
        state['source_image_mime_type'] = None
    return state


def resize_image_node(state: schema.ImageEditState) -> schema.ImageEditState:
    """Resize the source image to target dimensions"""
    print("🔄 Resizing source image...")

    if state.get('target_width', None) is None and state.get('target_height', None) is None:
        print("  ⏭️ No target dimensions specified, skipping resizing.")
        return state

    try:
        target_width = state.get('target_width', 1024)
        target_height = state.get('target_height', 1024)
        resized_image_data = services.pad_and_resize_image(
            image_data=state['source_image_data'],
            mime_type=state['source_image_mime_type'],
            target_width=target_width,
            target_height=target_height
        )
        state['source_image_data'] = resized_image_data
        print(f"✓ Image resized to {target_width}x{target_height} pixels")
    except Exception as e:
        print(f"⚠️ Image resizing failed: {str(e)}")
        state['error'] = str(e)
    return state


def create_agent():
    # Build the workflow graph
    workflow = StateGraph(schema.ImageEditState)

    # Add nodes
    workflow.add_node("improve_prompt", improve_prompt_node)
    workflow.add_node("load_image", load_image_node)
    workflow.add_node("resize_image", resize_image_node)
    workflow.add_node("edit_image", edit_image_node)

    # Define the flow
    workflow.set_entry_point("improve_prompt")
    workflow.add_edge("improve_prompt", "load_image")
    workflow.add_edge("load_image", "resize_image")
    workflow.add_edge("resize_image", "edit_image")
    workflow.add_edge("edit_image", END)

    # Compile the graph
    app = workflow.compile()
    return app
