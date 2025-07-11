from filerix.exceptions import PathValidationError
from filerix.utils import (
    _validate_path, _ensure_directory,
    _sanitize_content
)

from typing import Union, Optional 
from pathlib import Path 

def create_file(path: Union[str, Path], content: Optional[Union[str, bytes, dict, list, int, float, bool]] = '', *, overwrite: bool = True, compact: bool = False, encoding: str = 'utf-8') -> Path:
    """
    Cria um arquivo no caminho especificado com conteúdo opcional.
    
    Args:
        path (Union[str, Path]): Caminho completo onde o arquivo será criado.
        content (Any): Conteúdo a ser escrito (str, bytes, JSON, etc).
        overwrite (bool): Se False, impede sobrescrita de arquivos existentes.
        compact (bool): Se True, aplica sanitização compacta no conteúdo.
        encoding (str): Codificação usada na escrita do conteúdo. 
    
    Returns:
        Path: Caminho do arquivo criado (absoluto).
    
    Raises: 
        PathValidationError: Em caso de erros de validação, escrita ou permissões.
        TypeError: Se o conteúdo for de tipo não suportado.
        ValueError: Se o conteúdo sanitizado for inválido.
    """
    
    try:
        # Garante que o path é um objeto Path válido 
        path = Path(path).expanduser().resolve(strict = False)

        # Evita sobrescrita indesejada 
        if path.exists() and not overwrite:
            raise PathValidationError(str(path), 'O arquivo já existe e sobrescrita não é permitida.')

        # Garante que o diretório pai existe 
        _ensure_directory(path.parent)
        
        # Sanitiza o conteúdo (opcionalmente compacto)
        safe_content = _sanitize_content(content, compact = compact)

        # Escreve o conteúdo no arquivo (UTF-8 ou outro)
        path.write_text(safe_content, encoding = encoding)

        return path 
    except (TypeError, ValueError) as error:
        raise error # Erros da função _sanitize_content()
    except PathValidationError:
        raise 
    except PermissionError:
        raise PathValidationError(str(path), 'Permissão negada para criar o arquivo.')
    except IsADirectoryError:
        raise PathValidationError(str(path), 'O caminho especificado é um diretório.')
    except Exception as error:
        raise PathValidationError(str(path), f'Erro desconhecido ao criar o arquivo: {error}')

def read_file(path: Union[str, Path], *, as_bytes: bool = False, encoding: str = 'utf-8') -> Union[str, bytes]:
    """
    Lê o conteúdo de um arquivo. 
    
    Args:
        path (Union[str, Path]): Caminho do arquivo.
        as_bytes (bool): Se True, lê como bytes. Se False, como string.
        encoding (str): Codificação usada ao ler texto.
    
    Returns:
        str | bytes: Conteúdo lido do arquivo 
    
    Raises:
        PathValidationError: Se o caminho for inválido ou não for arquivo.
        FileNotFoundError: Se o arquivo não existir.
        UnicodeDecodeError: Se falhar ao decodificar com a codificação dada.
        PermissionError: Se não for possível ler o arquivo. 
    """

    try:
        file_path = _validate_path(path, must_exist = True, is_file = True, readable = True)
        if as_bytes:
            return file_path.read_bytes()
        return file_path.read_text(encoding = encoding)
    except FileNotFoundError:
        raise FileNotFoundError(f'Arquivo não encontrado: {path}')
    except PermissionError:
        raise PathValidationError(str(path), 'Sem permissão para leitura do arquivo')
    except UnicodeDecodeError:
        raise UnicodeDecodeError('Falha ao decodificar o conteúdo com a codificação passada')
    except PathValidationError:
        raise 
    except Exception as error:
        raise PathValidationError(str(path), f'Erro ao ler o arquivo: {error}')

def delete_file(path: Union[str, Path], *, ignore_missing: bool = False) -> bool:
    """
    Deleta um arquivo do sistema de arquivos. 
    
    Args: 
        path (Union[str, Path]): Caminho do arquivo a ser deletado. 
        ignore_missing (bool): Se True, não levanta erro se o arquivo não existir.
    
    Returns:
        bool: True se o arquivo foi deletado, False se ele não existir e ignore_missing=False.
    
    Raises:
        PathValidationError: Se o caminho for inválido ou não for um arquivo.
        PermissionError: Se não houver permissão para deletar.
        FileNotFoundError: Se o arquivo não existir (ignore_missing=False).
    """

    try:
        # Se não for ignorar inexistência, validar normalmente
        file_path = _validate_path(path, must_exist = True, is_file = True)
        file_path.unlink() 
        return True 
    except FileNotFoundError:
        if ignore_missing:
            return False 
        raise FileNotFoundError(f'O arquivo não foi encontrado')
    except IsADirectoryError:
        raise PathValidationError(str(path), 'O caminho especificado é um diretório')
    except PermissionError:
        raise PathValidationError(str(path), 'Sem permissão para deletar o arquivo')
    except PathValidationError:
        raise 
    except Exception as error:
        raise PathValidationError(str(path), f'Erro ao deletar o arquivo: {error}')
