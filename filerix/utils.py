from filerix.exceptions import PathValidationError
from typing import Union, Optional, Any
import tempfile, ctypes, json 
import stat, os, sys, re
from pathlib import Path 

def _sanitize_content(content: Any, *, compact: bool = False) -> str:
    """
    Limpa e padroniza o conteúdo a ser escrito em um arquivo. 
    
    Args:
        content (Any): O conteúdo bruto (str, int, float, bool, dict, etc).
        compact (bool): Se True, remove quebras de linha múltiplas e espaços redundantes.
    
    Returns:
        str: Conteúdo sanitizado e convertido em string.

    Raises:
        TypeError: Se o tipo do conteúdo não puder ser convertido.
        ValueError: Se o conteúdo for inválido ou vazio após a sanitização
    """

    # Converter o conteúdo para uma string segura 
    if isinstance(content, (dict, list)):
        try:
            content_str = json.dumps(content, ensure_ascii = False, indent = None if compact else 2)
        except Exception as error:
            raise TypeError(f'Falha ao converter estrutura JSON: {error}')
    elif isinstance(content, (str, int, float, bool, type(None))):
        content_str = str(content)
    elif isinstance(content, bytes):
        try:
            content_str = content.decode('utf-8')
        except UnicodeDecodeError:
            raise TypeError('Bytes devem estar codificados em UTF-8')
    else:
        raise TypeError(f'Tipo de conteúdo não suportado: {type(content)}')

    # Remover caracteres de controle invisíveis (exceto \t e \n)
    content_str = re.sub(r'[^\x20-\x7E\t\n]', '', content_str)

    # Padronizar as quebras de linha 
    content_str = content_str.replace('\r\n', '\n').replace('\r', '\n')

    if compact:
        # Remove quebras múltiplas e espaços duplicados 
        content_str = re.sub(r'\n{2,}', '\n', content_str)
        content_str = re.sub(r'[ \t]+', ' ', content_str).strip()

    if not content_str.strip():
        raise ValueError('O conteúdo final está vazio após a sanitização')

    return content_str

def is_readonly(path: Union[str, Path]) -> bool:
    """
    Verifica se o caminho é somente leitura (sem permissão de escrita)

    Args:
        path (Union[str, Path]): Caminho do arquivo ou diretório.
    
    Returns: 
        bool: True se for somente leitura, False caso contrário.
    
    Raises:
        TypeError: Se o caminho não for string ou Path.
        FileNotFoundError: Se o caminho não existir.
    """
    
    if not isinstance(path, (str, Path)):
        raise TypeError('O caminho deve ser uma string ou Path')

    path = Path(path).expanduser().resolve()
    
    if not path.exists():
        raise FileNotFoundError(f'O caminho não existe: {path}')

    if sys.platform != 'win32':
        return not os.access(path, os.W_OK)

    FILE_ATTRIBUTE_READONLY = 0x01 
    try:
        attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))
        if attrs == -1:
            raise OSError('Erro ao obter atributos do arquivo')
        return bool(attrs & FILE_ATTRIBUTE_READONLY)
    except Exception:
        # Fallback: Tenta com os.access 
        return not os.access(path, os.W_OK)

def _is_hidden(path: Union[str, Path]) -> bool:
    """
    Verifica se o caminho aponta para um arquivo ou diretório oculto.
    
    Args:
        path (Union[str, Path]): Caminho a ser verificado. 
        
    Returns: 
        bool: True se for oculto, False caso contrário.
    
    Raises: 
        TypeError: Se o argumento não for string ou Path.
        FileNotFoundError: Se o caminho não existir.
    """

    if not isinstance(path, (str, Path)):
        raise TypeError('O caminho deve ser uma string ou Path')

    path = Path(path).expanduser().resolve()
    
    if not path.exists():
        raise FileNotFoundError(f'O caminho não existe: {path}')

    # Unix - Oculto se começar com '.'
    if sys.platform != 'win32':
        return path.name.startswith('.')

    # Windows - Verifica atributo de arquivo oculto 
    FILE_ATTRIBUTE_HIDDEN = 0x02 
    
    try:
        attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))
        if attrs == -1:
            raise OSError('Erro ao obter atributos do arquivo.')
        return bool(attrs & FILE_ATTRIBUTE_HIDDEN)
    except Exception:
        # Fallback: Verifica prefixo no Windows também 
        return path.name.startswith('.')

def _get_tempfile(prefix: str = 'tmp_', suffix: str = '.tmp', dir: Optional[Union[str, Path]] = None, close_file: bool = True) -> Path:
    """
    Cria um arquivo temporário com nome único e retorna o caminho. 
    
    Args:
        preffix (str): Prefixo do nome do arquivo. Default: 'tmp_'.
        suffix (str): Sufixo (extensão) do arquivo. Default: '.tmp'.
        dir (Optional[Union[str, Path]]): Diretório onde o arquivo será criado.
                                          Se None, usa o diretório padrão do sistema.
        close_file (bool): Se True, fecha o arquivo imediatamente após a criação.
                           Se False, o arquivo continua aberto (o caller deve fechar)
    
    Returns:
        Path: Caminho para o arquivo temporário criado 
    
    Raises:
        PathValidationError: Se falhar ao criar o arquivo temporário
    """

    if dir is not None:
        dir = Path(dir).expanduser().resolve()
        
        try:
            if not dir.exists():
                dir.mkdir(parents = True, exist_ok = True)
            if not dir.is_dir():
                raise PathValidationError(str(dir), 'O caminho específico não é um diretório')
        except Exception as error:
            raise PathValidationError(str(dir), f'Erro ao preparar diretório temporário: {error}')

    try:
        temp = tempfile.NamedTemporaryFile(prefix = prefix, suffix = suffix, dir = str(dir) if dir else None, delete = False)
        path = Path(temp.name).resolve() 
        if close_file:
            temp.close()
        return path 
    except Exception as error:
        raise PathValidationError('<tempfile>', f'Erro ao criar arquivo temporário: {error}')



def _validate_path(path: Union[str, Path], *, must_exist: bool = True, is_file: Optional[bool] = None, readable: bool = False, writable: bool = False, allow_hidden: bool = True) -> Path:
    """
    Valida um caminho de arquivo ou diretório 
    
    Args:
        path (Union[str, Path]): Caminho a ser validado 
        must_exist (bool): Se True, o caminho deve existir. Default é True.
        is_file (Optional[bool]): Se definido, o caminho deve ser arquivo (True)
        readable (bool): Se True, verifica se o caminho é legível. 
        writable (bool): Se True, verifica se o caminho é gravável.
        allow_hidden (bool): Se False, rejeita arquivos/diretórios ocultos (prefixados com '.').
    
    Returns:
        Path: O caminho balidado, convertido para objeto Path.
        
    Raises:
        PathValidationError: Se qualquer validação falhar 
        TypeError: Se otipo de `path` for inválido.
    """
    
    if not isinstance(path, (str, Path)):
        raise TypeError('O caminho deve ser uma string ou caminho')

    path = Path(path).expanduser().resolve()
    
    if must_exist and not path.exists():
        raise PathValidationError(str(path), 'O caminho não existe')

    if is_file is not None:
        if is_file and not path.is_file():
            raise PathValidationError(str(path), 'Esperado arquivo, mas não é.')
        elif not is_file and not path.is_dir():
            raise PathValidationError(str(path), 'Esperado diretório, mas não é.')
    
    if not allow_hidden and path.name.startswith('.'):
        raise PathValidationError(str(path), 'O caminho é oculto e não é permitido.')

    if readable:
        if not os.access(path, os.R_OK):
            raise PathValidationError(str(path), 'O caminho não é legível.')

    if writable:
        if not os.access(path, os.W_OK):
            raise PathValidationError(str(path), 'O caminho não é gravável.')
    
    return path 

def _ensure_directory(directory: Union[str, Path], *, create_if_missing: bool = True, exist_ok: bool = True) -> Path:
    """
    Garante que um diretório existe. Se não existir, tenta criá-lo
   
    Args:
        directory (Union[str, Path]): Caminho do diretório.
        create_if_missing (bool): Se True, cria o diretório caso não exista.
        exist_ok (bool): Se False, levanta erro se o diretório já existir.
    
    Returns:
        Path: Objeto Path do diretório validado ou criado.
    
    Raises:
        PathValidationError: Se o caminho for inválido ou a criação falha
        TypeError: Se o argumento não for uma string ou Path.
    """
    
    if not isinstance(directory, (str, Path)):
        raise TypeError('O diretório deve ser uma string ou Path')

    directory = Path(directory).expanduser().resolve()

    if directory.exists():
        if not directory.is_dir():
            raise PathValidationError(str(directory), 'O caminho existe, mas não é um diretório')
        if not exist_ok:
            raise PathValidationError(str(directory), 'O diretório já existe')
        return directory 

    if not create_if_missing:
        raise PathValidationError(str(directory), 'O diretório não existe e não é permitido criar')

    try:
        directory.mkdir(parents = True, exist_ok = exist_ok)
    except PermissionError:
        raise PathValidationError(str(directory), 'Permissão negada para criar o diretório')
    except OSError as error:
        raise PathValidationError(str(directory), f'Erro ao criar o diretório: {error}')

    return directory 

