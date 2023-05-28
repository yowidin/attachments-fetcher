# Attachments Fetcher
A tool for downloading embedded images in a Markdown document into a dedicated directory and replacing the image links
with the local (fetched) ones.

## Usage example

For example, if you have a Markdown called `input.md`, with the following contents:

```markdown
Hello world!
![image](https://example.com/image/storage/sample.png)
```

After running this script against it:

```shell
af-make-local -i input.md -o output.md -m ./media
```

You will find a new file called `output.md` with the following content:

```markdown
Hello world!
![image](./media/sample.png)
```

and a `sample.png` image file, stored in the `./media` directory.
