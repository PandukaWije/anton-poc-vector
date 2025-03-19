import json

def json_to_markdown_table(json_data):
    # Extract headers from the first product with variants
    headers = ['Product Name', 'Size', 'Unit', 'Color', 'Price', 'Product Code']
    
    # Create markdown table header
    markdown = f"| {' | '.join(headers)} |\n"
    markdown += f"|{'|'.join(['---' for _ in headers])}|\n"

    # Process each product
    for product in json_data:
        product_data = product.get('product_data', {})
        product_name = product_data.get('main_product', '')
        variants = product_data.get('product_variants', [])
        
        # Add each variant as a row
        for variant in variants:
            if not isinstance(variant, dict):
                continue
                
            row = [
                product_name,
                variant.get('size', ''),
                variant.get('unit', ''),
                variant.get('color', ''),
                str(variant.get('price', '')),
                variant.get('product_code', '')
            ]
            # Replace None values with empty string
            row = [str(cell) if cell is not None else '' for cell in row]
            markdown += f"| {' | '.join(row)} |\n"
    
    return markdown

# Load your JSON data
with open('anton_products.json', 'r', encoding='utf-8') as file:
    json_data = json.load(file)

# Convert to markdown and save
markdown_table = json_to_markdown_table(json_data)
with open('anton_json_products.md', 'w', encoding='utf-8') as file:
    file.write(markdown_table)