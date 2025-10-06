#!/usr/bin/env python3
"""
Furniture Scene Generator - Python Version
Generates room scenes for furniture products using Google's Imagen API
Customized for Overstock White Label Project
"""

from furniture_scene_generator import llm, services, config
import pandas as pd

from pathlib import Path
import time
import sys

def main():
    """Main processing function"""
    print("=" * 70)
    print("🪑 FURNITURE SCENE GENERATOR - Overstock White Label Project")
    print("=" * 70)
    
    try:
        # Create output directory
        output_dir = Path('./output')
        output_dir.mkdir(exist_ok=True)
        
        # Initialize Google Cloud clients
        print("\n🔧 Initializing Google Cloud clients...")
        vision_client, imagen_model = services.initialize_google_clients()
        print("✓ Clients initialized")

        agent = llm.create_agent()
        

        df = services.read_excel_file()
        
        # Verify required columns
        required_columns = ['WL', 'Silo Image', 'Lifestyle Image']
        for col in required_columns:
            if col not in df.columns:
                raise Exception(f"Column '{col}' not found in Excel file")
        
        print("\n📊 Processing products...\n")
        
        # Track statistics
        processed = 0
        skipped = 0
        errors = 0
        
        # Process each product
        for idx, row in df.iterrows():
            wl_model = row['WL']
            silo_image_url = row['Silo Image']
            website_link = row.get('WebSite Link for Context', '')
            existing_lifestyle = row.get('Lifestyle Image', '')

            product_data = services.row_to_product_data(row)
            
            print(f"[{idx + 1}/{len(df)}] Processing: {wl_model}")
            if 'Model' in df.columns:
                print(f"  Model: {row['Model']}")
            
            try:
                # Skip if missing data
                if pd.isna(wl_model) or pd.isna(silo_image_url) or not wl_model or not silo_image_url:
                    print("  ⏭️  Missing WL model or silo image, skipping...")
                    skipped += 1
                    continue
                
                # Skip if already has lifestyle image
                if not pd.isna(existing_lifestyle) and str(existing_lifestyle).strip():
                    print("  ⏭️  Already has lifestyle image, skipping...")
                    skipped += 1
                    continue
                
                # Step 1: Analyze product image
                # No action needed, agent handles this

                
                # Step 2: Generate prompt
                prompt = services.create_place_image_in_room_prompt()
                
                # Step 3: Generate room scene
                output_filename = f"{wl_model}_room.png"
                local_output_path = output_dir / output_filename
                services.generate_room_scene_with_agent(agent, prompt, product_data, str(local_output_path))
                
                # Step 4: Upload to SFTP
                public_url = services.upload_to_sftp(str(local_output_path), output_filename)
                
                # Step 5: Update DataFrame
                df.at[idx, 'Lifestyle Image'] = public_url
                
                print(f"  ✅ SUCCESS! Image URL: {public_url}")
                processed += 1
                
                # Add delay to respect rate limits
                if idx < len(df) - 1:
                    print("  ⏱️  Waiting 2 seconds before next product...")
                    time.sleep(2)
                
            except Exception as e:
                print(f"  ❌ FAILED: {str(e)}")
                df.at[idx, 'Lifestyle Image'] = f"ERROR: {str(e)}"
                errors += 1
                continue
        
        # Save updated Excel file
        print(f"\n💾 Writing updated Excel file...")
        df.to_excel(config.EXCEL_OUTPUT_PATH, index=False)
        print(f"✓ Excel file updated: {config.EXCEL_OUTPUT_PATH}")
        
        # Print summary
        print("\n" + "=" * 70)
        print("📊 PROCESSING COMPLETE - SUMMARY")
        print("=" * 70)
        print(f"✅ Successfully processed: {processed} products")
        print(f"⏭️  Skipped: {skipped} products")
        print(f"❌ Errors: {errors} products")
        print(f"📁 Output file: {config.EXCEL_OUTPUT_PATH}")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()