import uuid
from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import F
from igreja.models import Igreja, Oferta, Dizimo
from accounts.models import Usuario


def validate_cpf(value):
    if not value.isdigit():
        raise ValidationError('O CPF deve conter apenas números.')
    if len(value) != 11:
        raise ValidationError('O CPF deve ter 11 dígitos.')
    
    # Lógica para validação do CPF
    
    # Se o CPF é inválido
    if invalid:
        raise ValidationError('CPF inválido.')

def validate_data(value):
    if value is not None:
        if not isinstance(value, str):
            value = value.strftime('%Y-%m-%d')
        try:
            datetime.datetime.strptime(value, '%Y-%m-%d')
        except ValueError:
            raise ValidationError('Data de nascimento inválida')


class Saida(models.Model):
    """
    Classe que representa uma saída de finança.
    Attributes:
        descricao (str): A descrição da saída.
        valor (DecimalField): O valor da saída.
    """
    id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False
    )
    
    data = models.DateField(
        validators=[validate_data]
    )
    
    descricao = models.TextField(
        max_length=200, 
    )
    
    valor = models.DecimalField(
        max_digits=10, 
        decimal_places=2
    )
    
    igreja = models.ForeignKey(
        Igreja, 
        related_name='saidas', 
        on_delete=models.CASCADE, 
    )
    
    REQUIRED_FIELDS = ['descricao', 'data', 'valor', 'igreja']
    
    def __str__(self):
        return "Saída -" + self.data

    def gerar_relatorio(self, **kargs):
        return "Gerar Relatorio"


class Entrada(models.Model):
    
    # função F para referenciar os campos valor_culto e valor_dizimo
    total = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=F('ofertas.total') + F('dizimos.valor')
    )
    
    ofertas = models.ForeignKey(
        Oferta, 
        related_name='Entrada_oferta', 
        on_delete=models.CASCADE, 
    )
    
    dizimos = models.ForeignKey(
        Dizimo, 
        related_name='Entrada_dizimo', 
        on_delete=models.CASCADE, 
    )
    
    igreja = models.ForeignKey(
        Igreja, 
        related_name='entradas', 
        on_delete=models.CASCADE, 
    )
    
    def __str__(self):
        return "Entrada -" + self.data
    
    def gerar_relatorio(self, **kargs):
        return "Gerar Relatorio"


class RelatorioGeral(models.Model):
    """
    Modelo para relatório geral de entrada e saída de caixa.
    """

    saldo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Saldo',
    )
    
    data_inicio = models.DateField(
        validators=[validate_data]
    )

    data_fim = models.DateField(
        validators=[validate_data]
    )

    entradas_sede = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Entradas Sede',
    )

    entradas_locais = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Entradas Locais',
    )

    entradas_missoes = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Entradas Missões',
    )
    
    saidas_sede = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='Saídas Sede',
    )

    saidas_locais = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='Saídas Locais',
    )

    pgto_obreiros = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='Pagamento de Obreiros',
    )

    inss = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='INSS',
    )

    aluguel_obreiros = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='Aluguel de Obreiros',
    )

    construcoes = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='Construções',
    )

    assis_social = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='Assistência Social',
    )    
    
    tesoureiro_sede = models.ForeignKey(
        Usuario, 
        related_name='relatorio_geral', 
        on_delete=models.DO_NOTHING, 
    )

    def __str__(self):
        """
        Retorna a representação do objeto em forma de string.
        """
        return f"Relatório: {self.data_inicio} - {self.data_fim}"

    def baixar(self):
        return "Baixar Relatório"
    
    def enviar(self):
        return "Enviar Relatório"

      
class RelatorioMensal(models.Model):
    
    data = models.DateField(
        validators=[validate_data]
    )
    
    pagamento_obreiro = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=F('entradas.total')*0.1
    )
    
    missoes_sede = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=F('entradas.total')*0.1
    )
    
    fundo_convencional = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=F('entradas.total')*0.05
    )
    
    saldo = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=F('entradas.total')-F('fundo_convencional')-F('missoes_sede')-F('pagamento_obreiro')-F('saidas.total')
    )
    
    igreja = models.ForeignKey(
        Igreja, 
        related_name='relatorio_mensal', 
        on_delete=models.CASCADE, 
    )
    
    entradas = models.ForeignKey(
        Entrada, 
        related_name='relatorio_mensal_entradas', 
        on_delete=models.CASCADE, 
    )
    
    saidas = models.ForeignKey(
        Saida, 
        related_name='relatorio_mensal_saidas', 
        on_delete=models.CASCADE, 
    )
     
    tesoureiro_sede = models.ForeignKey(
        Usuario, 
        related_name='relatorio_mensal_tesoureiro_sede', 
        on_delete=models.DO_NOTHING, 
    )
       
    def __str__(self):
            return "Relatório Mensal -" + self.data
        
    def baixar(self):
        return "Baixar Relatório"
    
    def enviar(self):
        return "Enviar Relatório"
    

