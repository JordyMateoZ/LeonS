"""Generador mínimo de PDF sin dependencias externas.

Suficiente para el carnet/constancia de una solicitud. Si el curso exige un
PDF más elaborado, se reemplaza por este adaptador sin tocar los routers.
"""

from __future__ import annotations


def _escapar(texto: str) -> bytes:
    datos = texto.encode("cp1252", errors="replace")
    return datos.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")


def construir_pdf(titulo: str, lineas: list[str]) -> bytes:
    contenido = bytearray()
    contenido += b"BT /F1 16 Tf 50 790 Td (" + _escapar(titulo) + b") Tj ET\n"
    contenido += b"BT /F2 11 Tf 50 760 Td 16 TL\n"
    for linea in lineas:
        if not linea:
            contenido += b"T*\n"
        else:
            contenido += b"(" + _escapar(linea) + b") Tj T*\n"
    contenido += b"ET\n"

    objetos = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            b"/Resources << /Font << /F1 5 0 R /F2 6 0 R >> >> /Contents 4 0 R >>"
        ),
        b"<< /Length " + str(len(contenido)).encode() + b" >>\nstream\n" + bytes(contenido) + b"endstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
    ]

    salida = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets: list[int] = []
    for numero, objeto in enumerate(objetos, start=1):
        offsets.append(len(salida))
        salida += f"{numero} 0 obj\n".encode() + objeto + b"\nendobj\n"

    inicio_xref = len(salida)
    salida += f"xref\n0 {len(objetos) + 1}\n".encode()
    salida += b"0000000000 65535 f \n"
    for offset in offsets:
        salida += f"{offset:010d} 00000 n \n".encode()
    salida += (
        f"trailer\n<< /Size {len(objetos) + 1} /Root 1 0 R >>\n"
        f"startxref\n{inicio_xref}\n%%EOF\n"
    ).encode()
    return bytes(salida)
