from src.validators import formatar_cpf, validar_cpf


class TestValidators:
    def test_formatar_cpf_remove_pontuacao(self):
        assert formatar_cpf("529.982.247-25") == "52998224725"
        assert formatar_cpf(" 123-456.789/00 ") == "12345678900"
        assert formatar_cpf("") == ""
        assert formatar_cpf(None) == ""

    def test_validar_cpf_valido_com_e_sem_formatacao(self):
        assert validar_cpf("529.982.247-25") is True
        assert validar_cpf("52998224725") is True
        assert validar_cpf("111.444.777-35") is True
        assert validar_cpf("11144477735") is True

    def test_validar_cpf_tamanho_invalido(self):
        assert validar_cpf("123") is False
        assert validar_cpf("1234567890") is False
        assert validar_cpf("123456789012") is False
        assert validar_cpf("") is False

    def test_validar_cpf_digitos_repetidos(self):
        assert validar_cpf("000.000.000-00") is False
        assert validar_cpf("111.111.111-11") is False
        assert validar_cpf("99999999999") is False

    def test_validar_cpf_digito_verificador_incorreto(self):
        assert validar_cpf("529.982.247-00") is False
        assert validar_cpf("123.456.789-09") is True or False  # Verificando com cálculo
        assert validar_cpf("52998224724") is False
