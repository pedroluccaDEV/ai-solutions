"""
Utilitários para processamento de diferentes tipos de arquivos
Suporta imagens, áudios e documentos
"""

import os
import base64
from typing import Optional, Dict, Any
from loguru import logger
from PIL import Image
import io


class FileProcessor:
    """Processador genérico de arquivos"""
    
    @staticmethod
    def read_file_as_base64(file_path: str) -> str:
        """
        Lê um arquivo e retorna em base64
        Útil para envio de arquivos para APIs
        """
        try:
            with open(file_path, 'rb') as f:
                return base64.b64encode(f.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"Erro ao ler arquivo como base64: {e}")
            raise


class ImageProcessor:
    """Processador especializado para imagens"""
    
    @staticmethod
    def get_image_info(file_path: str) -> Dict[str, Any]:
        """
        Extrai informações da imagem
        Returns: Dicionário com width, height, format, mode
        """
        try:
            with Image.open(file_path) as img:
                return {
                    'width': img.width,
                    'height': img.height,
                    'format': img.format,
                    'mode': img.mode,
                    'size_bytes': os.path.getsize(file_path)
                }
        except Exception as e:
            logger.error(f"Erro ao processar imagem: {e}")
            return {}
    
    @staticmethod
    def resize_image(file_path: str, max_width: int = 1024, max_height: int = 1024) -> str:
        """
        Redimensiona a imagem mantendo aspect ratio
        Returns: Caminho do arquivo redimensionado
        """
        try:
            with Image.open(file_path) as img:
                # Calcular novo tamanho mantendo aspect ratio
                img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                
                # Salvar imagem redimensionada
                output_path = file_path.replace('.', '_resized.')
                img.save(output_path, optimize=True, quality=85)
                
                logger.info(f"Imagem redimensionada: {output_path}")
                return output_path
        except Exception as e:
            logger.error(f"Erro ao redimensionar imagem: {e}")
            return file_path
    
    @staticmethod
    def convert_to_base64(file_path: str, resize: bool = True) -> Dict[str, Any]:
        """
        Converte imagem para base64 com metadados
        Args:
            resize: Se True, redimensiona antes de converter
        Returns: Dict com base64, mime_type e metadados
        """
        try:
            # Redimensionar se necessário
            if resize:
                processed_path = ImageProcessor.resize_image(file_path)
            else:
                processed_path = file_path
            
            # Obter informações da imagem
            info = ImageProcessor.get_image_info(processed_path)
            
            # Converter para base64
            with open(processed_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            # Limpar arquivo temporário se foi redimensionado
            if resize and processed_path != file_path:
                try:
                    os.unlink(processed_path)
                except:
                    pass
            
            # Determinar MIME type
            mime_types = {
                'JPEG': 'image/jpeg',
                'PNG': 'image/png',
                'WEBP': 'image/webp',
                'GIF': 'image/gif'
            }
            mime_type = mime_types.get(info.get('format', ''), 'image/jpeg')
            
            return {
                'base64': image_data,
                'mime_type': mime_type,
                'width': info.get('width'),
                'height': info.get('height'),
                'format': info.get('format')
            }
        except Exception as e:
            logger.error(f"Erro ao converter imagem para base64: {e}")
            raise


class AudioProcessor:
    """Processador especializado para áudios"""
    
    @staticmethod
    def get_audio_info(file_path: str) -> Dict[str, Any]:
        """
        Extrai informações do arquivo de áudio
        Requer pydub: pip install pydub
        """
        try:
            from pydub import AudioSegment
            
            audio = AudioSegment.from_file(file_path)
            
            return {
                'duration_seconds': len(audio) / 1000.0,
                'channels': audio.channels,
                'frame_rate': audio.frame_rate,
                'sample_width': audio.sample_width,
                'size_bytes': os.path.getsize(file_path)
            }
        except ImportError:
            logger.warning("pydub não instalado - informações limitadas de áudio")
            return {
                'size_bytes': os.path.getsize(file_path)
            }
        except Exception as e:
            logger.error(f"Erro ao processar áudio: {e}")
            return {}
    
    @staticmethod
    def convert_to_base64(file_path: str) -> Dict[str, Any]:
        """
        Converte áudio para base64 com metadados
        Returns: Dict com base64, mime_type e metadados
        """
        try:
            # Obter informações do áudio
            info = AudioProcessor.get_audio_info(file_path)
            
            # Converter para base64
            with open(file_path, 'rb') as f:
                audio_data = base64.b64encode(f.read()).decode('utf-8')
            
            # Determinar MIME type baseado na extensão
            ext = os.path.splitext(file_path)[1].lower()
            mime_types = {
                '.mp3': 'audio/mpeg',
                '.wav': 'audio/wav',
                '.ogg': 'audio/ogg',
                '.m4a': 'audio/m4a',
                '.webm': 'audio/webm'
            }
            mime_type = mime_types.get(ext, 'audio/mpeg')
            
            return {
                'base64': audio_data,
                'mime_type': mime_type,
                'duration': info.get('duration_seconds'),
                'channels': info.get('channels'),
                'sample_rate': info.get('frame_rate')
            }
        except Exception as e:
            logger.error(f"Erro ao converter áudio para base64: {e}")
            raise


class DocumentProcessor:
    """Processador especializado para documentos"""
    
    @staticmethod
    def extract_text_from_pdf(file_path: str) -> str:
        """
        Extrai texto de um PDF
        Requer PyPDF2: pip install PyPDF2
        """
        try:
            from PyPDF2 import PdfReader
            
            reader = PdfReader(file_path)
            text = ""
            
            for page in reader.pages:
                text += page.extract_text() + "\n\n"
            
            logger.info(f"Texto extraído do PDF: {len(text)} caracteres")
            return text.strip()
        except ImportError:
            logger.error("PyPDF2 não instalado")
            raise
        except Exception as e:
            logger.error(f"Erro ao extrair texto do PDF: {e}")
            raise
    
    @staticmethod
    def extract_text_from_docx(file_path: str) -> str:
        """
        Extrai texto de um DOCX
        Requer python-docx: pip install python-docx
        """
        try:
            from docx import Document
            
            doc = Document(file_path)
            text = "\n\n".join([para.text for para in doc.paragraphs])
            
            logger.info(f"Texto extraído do DOCX: {len(text)} caracteres")
            return text.strip()
        except ImportError:
            logger.error("python-docx não instalado")
            raise
        except Exception as e:
            logger.error(f"Erro ao extrair texto do DOCX: {e}")
            raise
    
    @staticmethod
    def read_text_file(file_path: str) -> str:
        """
        Lê um arquivo de texto simples
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            logger.info(f"Arquivo de texto lido: {len(text)} caracteres")
            return text
        except Exception as e:
            logger.error(f"Erro ao ler arquivo de texto: {e}")
            raise
    
    @staticmethod
    def read_csv_file(file_path: str) -> str:
        """
        Lê um arquivo CSV e retorna como texto formatado
        Requer pandas: pip install pandas
        """
        try:
            import pandas as pd
            
            df = pd.read_csv(file_path)
            
            # Converter para texto formatado
            text = f"CSV com {len(df)} linhas e {len(df.columns)} colunas\n\n"
            text += f"Colunas: {', '.join(df.columns)}\n\n"
            text += df.to_string()
            
            logger.info(f"CSV lido: {len(df)} linhas")
            return text
        except ImportError:
            logger.error("pandas não instalado")
            raise
        except Exception as e:
            logger.error(f"Erro ao ler CSV: {e}")
            raise
    
    @staticmethod
    def extract_text(file_path: str, mime_type: str) -> str:
        """
        Extrai texto de documento baseado no tipo
        """
        ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if ext == '.pdf':
                return DocumentProcessor.extract_text_from_pdf(file_path)
            elif ext in ['.docx', '.doc']:
                return DocumentProcessor.extract_text_from_docx(file_path)
            elif ext in ['.txt', '.md']:
                return DocumentProcessor.read_text_file(file_path)
            elif ext == '.csv':
                return DocumentProcessor.read_csv_file(file_path)
            else:
                logger.warning(f"Tipo de documento não suportado: {ext}")
                return ""
        except Exception as e:
            logger.error(f"Erro ao extrair texto do documento: {e}")
            return ""


class FileProcessorFactory:
    """
    Factory para obter o processador adequado baseado no tipo de arquivo
    """
    
    @staticmethod
    def get_processor(file_type: str):
        """
        Retorna o processador adequado para o tipo de arquivo
        """
        processors = {
            'image': ImageProcessor,
            'audio': AudioProcessor,
            'document': DocumentProcessor
        }
        
        return processors.get(file_type, FileProcessor)
    
    @staticmethod
    def process_file(file_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa um arquivo e retorna dados úteis para o agente
        
        Args:
            file_info: Dict com original_name, temp_path, mime_type, file_type, size
        
        Returns:
            Dict com dados processados do arquivo
        """
        file_type = file_info.get('file_type')
        file_path = file_info.get('temp_path')
        
        result = {
            'original_name': file_info.get('original_name'),
            'file_type': file_type,
            'mime_type': file_info.get('mime_type'),
            'size': file_info.get('size')
        }
        
        try:
            if file_type == 'image':
                # Para imagens, incluir base64 e metadados
                image_data = ImageProcessor.convert_to_base64(file_path, resize=True)
                result.update({
                    'base64': image_data['base64'],
                    'width': image_data.get('width'),
                    'height': image_data.get('height')
                })
                
            elif file_type == 'audio':
                # Para áudios, incluir base64 e metadados
                audio_data = AudioProcessor.convert_to_base64(file_path)
                result.update({
                    'base64': audio_data['base64'],
                    'duration': audio_data.get('duration')
                })
                
            elif file_type == 'document':
                # Para documentos, extrair texto
                text = DocumentProcessor.extract_text(file_path, file_info.get('mime_type'))
                result.update({
                    'text': text,
                    'text_length': len(text)
                })
            
            logger.info(f"Arquivo processado com sucesso: {file_info.get('original_name')}")
            return result
            
        except Exception as e:
            logger.error(f"Erro ao processar arquivo {file_info.get('original_name')}: {e}")
            result['error'] = str(e)
            return result