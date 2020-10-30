import os
import zipfile
import olefile
import re


class DocxAttachmentsExtractor:
    """
    Extract attachments from docx files
    """
    def __init__(self):
        self.FILEEXT = re.compile(r"\.\w+")
        self.counter = 0

    @staticmethod
    def parse_ole_contents(stream):
        # original filename in ANSI starts at byte 7 and is null terminated
        stream = stream[6:]
        filename = ""
        for ord_chr in stream:
            if ord_chr == 0:
                break
            filename += chr(ord_chr)
        stream = stream[len(filename) + 1:]
        filesize = 0
        # original filepath in ANSI is next and is null terminated
        for ord_chr in stream:
            if ord_chr == 0:
                break
            filesize += 1
        # next 4 bytes is unused
        stream = stream[filesize + 1 + 4:]
        # size of the temporary file path in ANSI in little endian
        temporary_filepath_size = 0
        temporary_filepath_size |= stream[0] << 0
        temporary_filepath_size |= stream[1] << 8
        temporary_filepath_size |= stream[2] << 16
        temporary_filepath_size |= stream[3] << 24
        stream = stream[4 + temporary_filepath_size:]
        size = 0  # size of the contents in little endian
        size |= stream[0] << 0
        size |= stream[1] << 8
        size |= stream[2] << 16
        size |= stream[3] << 24
        stream = stream[4:]
        contents = stream[:size]  # contents
        return filename, contents

    def get_attachments(self, tmpdir: str, filename: str, parameters: dict):
        """
        Extract attachments from given file and save it in the tmpdir directory where the file is located
        This method can only be called on appropriate files,
        ensure that `can_extract` is True for given file.
        :param tmpdir: directory where file is located, all attached files should also be saved in this directory.
        :param filename: Name of the file from which you should extract attachments (not abs path, only file name, use
        os.path.join(tmpdir, filename) to obtain path)
        :param parameters: dict with different parameters for extracting
        :return: list of AttachedFile (name of original file and abs path to the saved attachment file)
        """
        result = []
        ext = filename[-5:]
        self.counter += 1

        if ext == '.docx':
            with zipfile.ZipFile(os.path.join(tmpdir, filename), 'r') as zfile:
                files = zfile.namelist()

                attachments = [file for file in files if file.startswith("word/media/")]
                attachments += [file for file in files if file.startswith("word/embeddings/")]

                for attachment in attachments:
                    namefile = os.path.split(attachment)[-1]
                    if not namefile.endswith('.emf') and not namefile.endswith('.bin'):
                        path = f"{tmpdir}/{namefile}"
                        with open(path, "wb") as write_file:
                            write_file.write(zfile.read(attachment))
                        result.append([namefile, path])

                    elif namefile.endswith('.bin'):
                        # extracting PDF-files
                        ole = olefile.OleFileIO(zfile.open(attachment).read())
                        if ole.exists("CONTENTS"):
                            data = ole.openstream('CONTENTS').read()
                            if data[0:5] == b'%PDF-':
                                path = f"{tmpdir}/{namefile[:-4] + str(self.counter) + '.pdf'}"
                                with open(path, "wb") as write_file:
                                    write_file.write(data)
                                result.append([namefile[:-4] + str(self.counter) + '.pdf', path])
                        # extracting files in other formats
                        elif ole.exists("\x01Ole10Native"):
                            data = ole.openstream("\x01Ole10Native").read()
                            filename, contents = self.parse_ole_contents(data)
                            path = f"{tmpdir}/{filename}"
                            with open(path, "wb") as write_file:
                                write_file.write(contents)
                            result.append([filename, path])

        return result


if __name__ == "__main__":
    tmp_dir = 'examples/tmp'
    names = []
    for i in os.listdir(tmp_dir):
        if i.endswith('.docx'):
            names.append(i)
    docx_attachments_extractor = DocxAttachmentsExtractor()
    for name in names:
        attachments = docx_attachments_extractor.get_attachments(tmp_dir, name, {})
        print(f"name = {name}\nattachments = {attachments}")
