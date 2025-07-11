import pytest, shutil, tempfile
import ctypes, stat, os
from pathlib import Path

from filerix.utils import (
    _validate_path, _ensure_directory,
    _get_tempfile, _is_hidden, _is_readonly,
    _sanitize_content
)

from filerix.exceptions import PathValidationError

### ----------- _validate_path() ----------- ###

def test_validate_existing_file(tmp_path):
    file = tmp_path / 'file.txt'
    file.write_text('Teste')
    result = _validate_path(file, must_exist = True, is_file = True)
    assert result == file.resolve() 

def test_validate_nonexistent_path():
    with pytest.raises(PathValidationError):
        _validate_path('não-existe.txt')

def test_validate_hidden_file(tmp_path):
    hidden = tmp_path / '.oculto'
    hidden.write_text('...')
    with pytest.raises(PathValidationError):
        _validate_path(hidden, allow_hidden = False)

def test_validate_permission_readonly(tmp_path):
    file = tmp_path / 'arquivo.txt'
    file.write_text('conteúdo')
    file.chmod(stat.S_IREAD)
    result = _validate_path(file, readable = True)
    assert result.exists()

def test_validate_invalid_type():
    with pytest.raises(TypeError):
        _validate_path(12345)

### ----------- _ensure_directory() ----------- ###

def test_ensure_existing_directory(tmp_path):
    result = _ensure_directory(tmp_path, exist_ok = True)
    assert result.exists() and result.is_dir() 

def test_ensure_create_directory(tmp_path):
    new_dir = tmp_path / 'novo'
    result = _ensure_directory(new_dir)
    assert result.exists() and result.is_dir() 

def test_ensure_directory_conflict_with_file(tmp_path):
    file = tmp_path / 'conflito'
    file.write_text('arquivo')
    with pytest.raises(PathValidationError):
        _ensure_directory(file)

### ----------- _get_tempfile() ----------- ###

def test_create_tempfile():
    temp_file = _get_tempfile()
    assert temp_file.exists()
    temp_file.unlink() 

def test_tempfile_with_prefix_suffix(tmp_path):
    temp_file = _get_tempfile(prefix = 'log_', suffix = '.log', dir = tmp_path)
    assert temp_file.name.startswith('log_') and temp_file.name.endswith('.log')
    assert temp_file.parent == tmp_path.resolve()
    temp_file.unlink()

### ----------- _is_hidden() ----------- ### 

def test_is_hidden_true(tmp_path):
    hidden = tmp_path / '.escondido'
    hidden.write_text('x')
    
    # Windows: Aplicar atributo oculto 
    if os.name == 'nt':
        FILE_ATTRIBUTE_HIDDEN = 0x02 
        ctypes.windll.kernel32.SetFileAttributesW(str(hidden), FILE_ATTRIBUTE_HIDDEN)
    
    assert _is_hidden(hidden) is True 

def test_is_hidden_false(tmp_path):
    visible = tmp_path / 'visível.txt'
    visible.write_text('x')
    assert _is_hidden(visible) is False 

### ----------- _is_readonly() ----------- ###

def test_is_readonly_true(tmp_path):
    file = tmp_path / 'ro.txt'
    file.write_text('Apenas leitura')
    file.chmod(stat.S_IREAD)
    assert _is_readonly(file) is True 

def test_is_readonly_false(tmp_path):
    file = tmp_path / 'escreve.txt'
    file.write_text('Pode escrever')
    assert _is_readonly(file) is False 

### ----------- _sanitize_content() ----------- ###

def test_sanitize_str():
    text = 'Linh\r\nNova\r\t'
    result = _sanitize_content(text)
    assert 'Linh\nNova' in result 

def test_sanitize_dict():
    data = {'Nome': 'Alecsander', 'Idade': 18}
    result = _sanitize_content(data)
    assert '"Nome": "Alecsander"' in result 

def test_sanitize_bytes():
    b = b'Isso \xe2\x9c\x94'
    result = _sanitize_content(b)
    assert 'Isso' in result 

def test_sanitize_compact():
    text = 'Linha 1\n\n\nLinha 2  \t  mais'
    result = _sanitize_content(text, compact = True)
    assert '\n\n' not in result 
    assert '  ' not in result 

def test_sanitize_unsupported_type():
    with pytest.raises(TypeError):
        _sanitize_content(object())

