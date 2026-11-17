from __future__ import annotations


def _escapar(texto: str) -> str:
    return (
        texto.replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
        .replace("\r\n", " ")
        .replace("\n", " ")
    )


def generar_pdf(titulo: str, lineas: list[str]) -> bytes:
    """Generador PDF mínimo (sin dependencias) para carné y contrato."""
    contenido = [
        "BT",
        "/F1 18 Tf",
        "72 770 Td",
        f"({_escapar(titulo)}) Tj",
        "/F1 11 Tf",
        "0 -30 Td",
    ]
    for linea in lineas[:45]:
        contenido.extend([f"({_escapar(linea)}) Tj", "0 -18 Td"])
    contenido.append("ET")
    flujo = "\n".join(contenido)

    objetos = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        f"<< /Length {len(flujo.encode('latin-1', 'replace'))} >>\nstream\n{flujo}\nendstream",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]

    pdf = "%PDF-1.4\n"
    desplazamientos: list[int] = []
    for indice, objeto in enumerate(objetos, start=1):
        desplazamientos.append(len(pdf.encode("latin-1", "replace")))
        pdf += f"{indice} 0 obj\n{objeto}\nendobj\n"

    inicio_xref = len(pdf.encode("latin-1", "replace"))
    pdf += f"xref\n0 {len(objetos) + 1}\n"
    pdf += "0000000000 65535 f \n"
    for desplazamiento in desplazamientos:
        pdf += f"{desplazamiento:010d} 00000 n \n"
    pdf += f"trailer\n<< /Size {len(objetos) + 1} /Root 1 0 R >>\n"
    pdf += f"startxref\n{inicio_xref}\n%%EOF"

    return pdf.encode("latin-1", "replace")
