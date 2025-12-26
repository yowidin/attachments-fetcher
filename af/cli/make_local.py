import argparse
import hashlib
import os
import re
import requests

from urllib.parse import quote, urlparse

IMAGE_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg']


def sanitize_filename(url: str) -> str:
    parsed = urlparse(url)
    _, ext = os.path.splitext(parsed.path)
    hash_part = hashlib.md5(url.encode('utf-8')).hexdigest()
    return f'{hash_part}{ext}' if ext else hash_part


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

    def replace_by_pattern(pattern: str, file_content):
        def replace_func(match):
            alt_text = match.group(1)
            url = match.group(2)
            target = match.group(3) if len(match.groups()) > 2 else None

            already_local = url.startswith(quote(media_dir))
            is_image = any(url.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg'])

            if already_local or not is_image:
                return f'![{alt_text}]({url})'

            # Extract the image filename from the URL
            filename = sanitize_filename(url)

            # Download the image
            image_path = os.path.join(media_dir, filename)
            download_image(url, image_path)

            # Replace the image link with the local file path
            local_path = quote(f"{media_dir}/{filename}")

            if target is None or target == url:
                return f'![{alt_text}]({local_path})'
            else:
                return f'[![{alt_text}]({local_path})]({target})'

        return re.sub(pattern, replace_func, file_content, flags=re.MULTILINE)

    # Replace image links:

    # - [![alt text](url)](url)
    nested_pattern = r"\[!\[(.*?)\]\((.*?)\)\]\((.*?)\)"
    content = replace_by_pattern(nested_pattern, content)

    # - ![alt text](url)
    simple_pattern = r"!\[(.*?)\]\((.*?)\)"
    content = replace_by_pattern(simple_pattern, content)

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
