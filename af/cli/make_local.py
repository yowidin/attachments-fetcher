import argparse
import os
import re
import requests

from urllib.parse import quote


def download_image(url, destination):
    print(f'Downloading: {url}')
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(destination, 'wb') as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)


def replace_image_links(md_file: str, output: str, media_dir: str, force: bool):
    if not os.path.isfile(md_file):
        raise RuntimeError(f'Input file not found: {md_file}')

    if os.path.isfile(output) and not force:
        raise RuntimeError(f'Output file already exists, use -f to override: {output}')

    # Create the output directory if it doesn't exist
    os.makedirs(media_dir, exist_ok=True)

    with open(md_file, 'r') as file:
        content = file.read()

    # Match image links in the Markdown file
    pattern = r"!\[(.*?)\]\((.*?)\)"
    matches = re.findall(pattern, content)

    for alt_text, url in matches:
        # Check if the URL has an image file extension
        if not any(url.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif']):
            continue

        # Extract the image filename from the URL
        filename = url.split("/")[-1]

        # Download the image
        image_path = os.path.join(media_dir, filename)
        download_image(url, image_path)

        # Replace the image link with the local file path
        local_path = quote(f"{media_dir}/{filename}")
        content = content.replace(url, local_path)

    # Write the updated content to a new Markdown file
    with open(output, 'w') as file:
        file.write(content)

    print("Image links replaced successfully!")
    print(f"Updated Markdown file saved as: {output}")


def main():
    parser = argparse.ArgumentParser('Attachments Fetcher')
    parser.add_argument('--input', '-i', type=str, required=True, help='Input file')
    parser.add_argument('--output', '-o', type=str, required=True, help='Output file')
    parser.add_argument('--media-dir', '-m', type=str, required=True, help='Directory to store downloaded images')
    parser.add_argument('--force', '-f', action='store_true', required=False, default=False,
                        help='Override existing output file')

    args = parser.parse_args()
    replace_image_links(args.input, args.output, args.media_dir, args.force)


if __name__ == '__main__':
    main()
