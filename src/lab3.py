import socket
import tkinter
import tkinter.font

def request(url):
    scheme, url = url.split("://", 1)
    assert scheme in ["http", "https"], \
        "Unknown scheme {}".format(scheme)

    host, path = url.split("/", 1)
    path = "/" + path
    port = 80 if scheme == "http" else 443

    if ":" in host:
        host, port = host.split(":", 1)
        port = int(port)

    s = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP)
    s.connect((host, port))

    if scheme == "https":
        ctx = ssl.create_default_context()
        s = ctx.wrap_socket(s, server_hostname=host)

    s.send(("GET {} HTTP/1.0\r\n".format(path) +
            "Host: {}\r\n\r\n".format(host)).encode("utf8"))
    response = s.makefile("r", encoding="utf8", newline="\r\n")

    statusline = response.readline()
    version, status, explanation = statusline.split(" ", 2)
    assert status == "200", "{}: {}".format(status, explanation)

    headers = {}
    while True:
        line = response.readline()
        if line == "\r\n": break
        header, value = line.split(":", 1)
        headers[header.lower()] = value.strip()

    body = response.read()
    s.close()

    return headers, body

class Text:
    def __init__(self, text):
        self.text = text

class Tag:
    def __init__(self, tag):
        self.tag = tag

def lex(source):
    out = []
    text = ""
    in_angle = False
    for c in source:
        if c == "<":
            in_angle = True
            if text: out.append(Text(text))
            text = ""
        elif c == ">":
            in_angle = False
            out.append(Tag(text))
            text = ""
        else:
            text += c
    return out

def layout(tokens):
    display_list = []

    x, y = 13, 13
    bold, italic = False, False
    terminal_space = True
    for tok in tokens:
        if isinstance(tok, Text):
            font = tkinter.font.Font(
                family="Times",
                size=16,
                weight=("bold" if bold else "normal"),
                slant=("italic" if italic else "roman"),
            )

            if tok.text[0].isspace() and not terminal_space:
                x += font.measure(" ")
            
            for word in tok.text.split():
                w = font.measure(word)
                if x + w > 787:
                    x = 13
                    y += font.metrics('linespace') * 1.2
                display_list.append((x, y, word, font))
                x += w + font.measure(" ")
            
            terminal_space = tok.text[-1].isspace()
            if not terminal_space:
                x -= font.measure(" ")
        elif isinstance(tok, Tag):
            if tok.tag == "i":
                italic = True
            elif tok.tag == "/i":
                italic = False
            elif tok.tag == "b":
                bold = True
            elif tok.tag == "/b":
                bold = False
            elif tok.tag == "/p":
                terminal_space = True
                x = 13
                y += font.metrics("linespace") * 1.2 + 16
    return display_list

def show(text):
    window = tkinter.Tk()
    canvas = tkinter.Canvas(window, width=800, height=600)
    canvas.pack()

    SCROLL_STEP = 100
    scrolly = 0
    display_list = layout(text)

    def render():
        canvas.delete("all")
        for x, y, c, font in display_list:
            canvas.create_text(x, y - scrolly, text=c, font=font, anchor="nw")

    def scrolldown(e):
        nonlocal scrolly
        scrolly += SCROLL_STEP
        render()

    window.bind("<Down>", scrolldown)
    render()

    tkinter.mainloop()

if __name__ == "__main__":
    import sys
    headers, body = request(sys.argv[1])
    show(lex(body))