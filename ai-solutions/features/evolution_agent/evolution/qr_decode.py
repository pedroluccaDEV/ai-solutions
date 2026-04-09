import base64
from io import BytesIO
from PIL import Image
import qrcode

def gerar_qr_whatsapp(data, salvar_como=None):
    """
    Gera um QR code a partir de base64 ou token da API do WhatsApp.
    
    :param data: Base64 da imagem ou token string.
    :param salvar_como: Caminho para salvar a imagem (opcional).
    :return: PIL.Image do QR code.
    """
    # Detecta se é base64 (começa com "data:image") ou token
    if data.startswith("data:image"):
        # Remove cabeçalho se existir
        header, base64_str = data.split(",", 1)
        qr_bytes = base64.b64decode(base64_str)
        img = Image.open(BytesIO(qr_bytes))
    else:
        # Assume que é token e gera QR code
        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    
    if salvar_como:
        img.save(salvar_como)
        print(f"QR code salvo em: {salvar_como}")
    
    img.show()
    return img

# Exemplo de uso:
# base64_qr = "data:image/png;base64,..."
# token = "123456abcdef"
# gerar_qr_whatsapp(base64_qr, salvar_como="qr.png")
# gerar_qr_whatsapp(token, salvar_como="qr_token.png")
