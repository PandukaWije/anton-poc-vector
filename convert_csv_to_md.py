import csv
import sys

def csv_to_markdown(csv_file, md_file):
    try:
        with open(csv_file, 'r', encoding='utf-8') as file:
            csv_reader = csv.reader(file)
            headers = next(csv_reader)  # Get the header row
            
            # Create markdown table header
            markdown_content = '| ' + ' | '.join(headers) + ' |\n'
            markdown_content += '|' + '|'.join(['---' for _ in headers]) + '|\n'
            
            # Add table rows
            for row in csv_reader:
                markdown_content += '| ' + ' | '.join(row) + ' |\n'
                
        # Write to markdown file
        with open(md_file, 'w', encoding='utf-8') as file:
            file.write(markdown_content)
            
        print(f"Successfully converted {csv_file} to {md_file}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
        
    csv_file = 'anton_products.csv'
    md_file = 'anton_csv_products.md'
    csv_to_markdown(csv_file, md_file)