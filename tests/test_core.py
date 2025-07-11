from filerix.exceptions import PathValidationError
from filerix.core import (
    create_file, read_file, delete_file
)

from pathlib import Path 
import pytest, stat, os 
import json

### ----------- create_file() ----------- ###

def test_create_file_with_text(tmp_path):
    path = tmp_path / 'arquivo.txt'
    created = create_file(path, 'Conteúdo')
    assert created.exists()
    assert created.read_text(encoding = 'utf-8') == 'Conteúdo'

def test_create_file_with_dict(tmp_path):
    path = tmp_path / 'dados.json'
    data = {'Nome': 'Alecsander', 'Idade': 18}
    created = create_file(path, data, compact = True)
    loaded = json.loads(path.read_text(encoding = 'utf-8'))
    assert loaded == data

def test_create_file_overwrite_false(tmp_path):
    path = tmp_path / 'fixo.txt'
    path.write_text('original')
    with pytest.raises(PathValidationError):
        create_file(path, 'novo', overwrite = False)

def test_create_file_invalid_content(tmp_path):
    path = tmp_path / 'invalido.txt'
    with pytest.raises(TypeError):
        create_file(path, object())

### ----------- read_file() ----------- ###

def test_read_file_text(tmp_path):
    path = tmp_path / 'lido.txt'
    text = 'Ler isso aqui'
    path.write_text(text, encoding = 'utf-8')
    result = read_file(path)
    assert result == text 

def test_read_file_bytes(tmp_path):
    path = tmp_path / 'binario.bin'
    data = b'\x00\x01\x02Hello'
    path.write_bytes(data)
    result = read_file(path, as_bytes = True)
    assert result == data

def test_read_file_inexistente(tmp_path):
    path = tmp_path / 'nada.txt'
    with pytest.raises(PathValidationError):
        read_file(path)

### ----------- delete_file() ----------- ###

def test_delete_existing_file(tmp_path):
    path = tmp_path / 'apagar.txt'
    path.write_text('Deleta isso')
    result = delete_file(path)
    assert result is True 
    assert not path.exists() 

def test_delete_missing_file_ignore_false(tmp_path):
    path = tmp_path / 'não-existe.txt'
    with pytest.raises(PathValidationError):
        delete_file(path, ignore_missing = False)

def test_delete_missing_file_ignore_true(tmp_path):
    path = tmp_path / 'sem-arquivo.txt'
    result = delete_file(path, ignore_missing = True)
    assert result is False 

def test_delete_directory_instead_of_file(tmp_path):
    dir_path = tmp_path / 'is_directory'
    dir_path.mkdir()
    with pytest.raises(PathValidationError):
        delete_file(dir_path)

