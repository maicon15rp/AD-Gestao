import io

from accounts.views import obterUsuario
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Q
from django.http import FileResponse, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, reverse
from igreja.forms import DizimoForm, OfertaForm
from igreja.models import Dizimo, Igreja, OfertaCulto
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from .forms import SaidaForm, RelatorioGeralForm
from .models import Entrada, RelatorioGeral, RelatorioMensal, Saida

pdfmetrics.registerFont(TTFont("Arial", "arial.ttf"))
from datetime import datetime
import calendar
from functools import partial

def atualizar_registro_model(financa, user):
    # Setando objetos
    relatorio_geral = RelatorioGeral.objects.get(status='ativo')
    relatorio_mensal = RelatorioMensal.objects.get(igreja=user.igreja, status='ativo')
    igreja = user.igreja
    saida = Saida.objects.last()

    if financa == 'saida':

        # Atualizando registros no model de RealatórioGeral
        relatorio_geral.saidas_sede = relatorio_geral.calc_saidas_sede
        relatorio_geral.saidas_locais = relatorio_geral.calc_saidas_locais
        relatorio_geral.saldo = relatorio_geral.calc_saldo

        relatorio_geral.save() 

        # Atualizando registros no model de RealatórioMensal
        relatorio_mensal.total_saidas = relatorio_mensal.calc_saidas
        relatorio_mensal.saldo = relatorio_mensal.calc_saldo
        relatorio_mensal.pagamento_obreiro = relatorio_mensal.calc_pagamento_obreiro
        relatorio_mensal.fundo_convencional = relatorio_mensal.calc_fundo_convencional
        relatorio_mensal.missoes_sede = relatorio_mensal.calc_missoes_sede

        relatorio_mensal.save() 

        # Atualizando registro de saldo no model de Igreja
        igreja.saldo = saida.calc_saldo
        print('saldo att')
        igreja.save()


    else:
        # Atualizando registros no model de RealatórioGeral
        relatorio_geral.entradas_sede = relatorio_geral.calc_entradas_sede
        relatorio_geral.entradas_locais = relatorio_geral.calc_entradas_locais
        relatorio_geral.saldo = relatorio_geral.calc_saldo

        relatorio_geral.save()  

        # Atualizando registros no model de RealatórioMensal
        relatorio_mensal.total_entradas = relatorio_mensal.calc_total_entradas
        relatorio_mensal.saldo = relatorio_mensal.calc_saldo
        relatorio_mensal.pagamento_obreiro = relatorio_mensal.calc_pagamento_obreiro
        relatorio_mensal.fundo_convencional = relatorio_mensal.calc_fundo_convencional
        relatorio_mensal.missoes_sede = relatorio_mensal.calc_missoes_sede

        relatorio_mensal.save() 

        # Atualizando registro de saldo no model de Igreja
        igreja.saldo = saida.calc_saldo
        print('saldo atualizado')
        igreja.save()


@login_required
@permission_required('accounts.tesoureiro')
def adicionar_saida(request):
    usuario = obterUsuario(request)
    if request.method == 'POST':
        
        form = SaidaForm(request.POST)
        if form.is_valid():
            form.instance.igreja = usuario.igreja
            saida = form.save()
            saida.save()            
            messages.success(request, 'Saída adicionada com sucesso!')
            context = {
                    'form': form,
                }
            return HttpResponseRedirect(reverse('listar_saida'))
    else:
        form = SaidaForm()
        
    context = {
        'usuario': usuario,
        'igreja': usuario.igreja,
        'form' : form,
    }
    
    return render(request, 'financas/saidas/adicionar.html', context)


@login_required
@permission_required('accounts.tesoureiro')
def editar_saida(request, saida_id):

    usuario = obterUsuario(request)
    saida = Saida.objects.get(id=saida_id)

    if request.method == "POST":
        form = SaidaForm(request.POST, instance=saida)
        
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('detalhar_saida', args=[saida.id]))
    else:
        form = SaidaForm(instance=saida)

    context = {
        'usuario': usuario,
        'igreja': usuario.igreja,
        'form' : form,
    }
    return render(request, 'financas/saidas/editar.html', context)


@login_required
@permission_required('accounts.tesoureiro')
def excluir_saida(request, saida_id):
    saida = Saida.objects.get(id=saida_id)
    saida.delete()

    return HttpResponseRedirect(reverse('listar_saida'))


@login_required
@permission_required('accounts.tesoureiro')
def listar_saida(request):
    usuario = obterUsuario(request)
    saidas = Saida.objects.filter(igreja=usuario.igreja)
    context = {
        'usuario': usuario,
        'igreja': usuario.igreja,
        'saidas': saidas
    }
    return render(request, 'financas/saidas/listar.html', context)


@login_required
@permission_required('accounts.tesoureiro')
def detalhar_saida(request, saida_id):

    usuario = obterUsuario(request)
    saida = Saida.objects.get(id=saida_id)
    context = {
        'usuario': usuario,
        'igreja': usuario.igreja,
        'saida': saida
    }
    return render(request, 'financas/saidas/detalhar.html', context)

@login_required
@permission_required('accounts.tesoureiro')
def adicionar_dizimo(request):
    usuario = obterUsuario(request)
    print(usuario.igreja)

    entrada = get_object_or_404(Entrada, igreja=usuario.igreja)

    formWithUser = partial(DizimoForm, usuario=usuario)
    if request.method == 'POST':
        
        form = formWithUser(request.POST)
        if form.is_valid():
            form.instance.igreja = usuario.igreja
            dizimo = form.save()
            dizimo.save()            
            messages.success(request, 'Dízimo adicionada com sucesso!')

            entrada.dizimos.add(dizimo)
            context = {
                    'form': form,
                }
            return HttpResponseRedirect(reverse('listar_dizimos'))
    else:
        form = formWithUser(usuario=usuario)
        
    context = {
        'usuario': usuario,
        'igreja': usuario.igreja,
        'form' : form,
    }
    
    return render(request, 'financas/entradas/dizimos/adicionar.html', context)


@login_required
@permission_required('accounts.tesoureiro')
def editar_dizimo(request, dizimo_id):

    usuario = obterUsuario(request)
    dizimo = Dizimo.objects.get(id=dizimo_id)

    if request.method == "POST":
        form = DizimoForm(request.POST, instance=dizimo)
        
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('detalhar_dizimo', args=[dizimo.id]))
    else:
        form = DizimoForm(instance=dizimo)

    context = {
        'usuario': usuario,
        'igreja': usuario.igreja,
        'form' : form,
    }
    return render(request, 'financas/entradas/dizimos/editar.html', context)


@login_required
@permission_required('accounts.tesoureiro')
def excluir_dizimo(request, dizimo_id):
    dizimo = Dizimo.objects.get(id=dizimo_id)
    dizimo.delete()

    return HttpResponseRedirect(reverse('listar_dizimos'))


@login_required
@permission_required('accounts.tesoureiro')
def listar_dizimos(request):
    usuario = obterUsuario(request)

    igreja = Igreja.objects.get(nome=usuario.igreja.nome)
  
    dizimos = igreja.dizimos.all()
    
    context = {
        'usuario': usuario,
        'igreja': usuario.igreja,
        'dizimos': dizimos
    }
    return render(request, 'financas/entradas/dizimos/listar.html', context)


@login_required
@permission_required('accounts.tesoureiro')
def detalhar_dizimo(request, dizimo_id):

    usuario = obterUsuario(request)
    dizimo = Dizimo.objects.get(id=dizimo_id)
    context = {
        'usuario': usuario,
        'igreja': usuario.igreja,
        'dizimo': dizimo
    }
    return render(request, 'financas/entradas/dizimos/detalhar.html', context)

# Esta função soma os valores dos dízimos de um culto, considerando o dia e tipo de culto do dízimo
def calc_soma_dizimo(oferta):
    # Busca todos os dízimos cuja data é a mesma do relatório de culto 
    dizimos = Dizimo.objects.filter(
    Q(data_culto=oferta.data_culto) & Q(igreja=oferta.igreja)
    )

    # Cria a variável "valor_dizimo"
    valor_dizimo = 0

    # Loop que irá percorrer todos os objetos filtrados, contidos em 'dizimos'
    for dizimo in dizimos:

        #verifica se o dizimo em questão possui tanto a mesma data quanto o tipo de culto do relatório criado
        if dizimo.tipo_culto == oferta.tipo_culto and dizimo.data_culto == oferta.data_culto:
            valor_dizimo = valor_dizimo + dizimo.valor

    return valor_dizimo

def adicionar_oferta(request):
    usuario = obterUsuario(request)
    entrada, _ = Entrada.objects.get_or_create(igreja=usuario.igreja) # (objeto, se ele existe ou não)
    
    if request.method == 'POST':
        
        form = OfertaForm(request.POST)
        if form.is_valid():
            
            # Atribui ao atributo 'igreja' da oferta a igreja do usuario que esta criando o relatório de oferta
            form.instance.igreja = usuario.igreja

            oferta = form.save()
            oferta.save()     

            # Chama a função que calcula a soma dos valores dos dizimos daquele culto
            valor_dizimo = calc_soma_dizimo(oferta=oferta)

            # Atribui ao atributo "valor_dizimo" o valor calculado anteriormento pela função
            oferta.valor_dizimo = valor_dizimo

            # Salva a nova atribuição
            oferta.save()

            messages.success(request, 'Oferta adicionada com sucesso!')

            entrada.ofertas.add(oferta)

            context = {
                    'form': form,
                }
            return HttpResponseRedirect(reverse('listar_ofertas'))
    else:
        form = OfertaForm()
        
    context = {
        'usuario': usuario,
        'igreja': usuario.igreja,
        'form' : form,
    }
    
    return render(request, 'financas/entradas/ofertas/adicionar.html', context)

def listar_ofertas(request):
    usuario = obterUsuario(request)

    igreja = Igreja.objects.get(nome=usuario.igreja.nome)
  
    ofertas = igreja.ofertas_culto.all()

    context = {
        'usuario': usuario,
        'igreja': usuario.igreja,
        'ofertas': ofertas
    }
    return render(request, 'financas/entradas/ofertas/listar.html', context)


def excluir_oferta(request, oferta_id):
    usuario = obterUsuario(request)
    oferta = OfertaCulto.objects.get(id=oferta_id)
    oferta.delete()

    return HttpResponseRedirect(reverse('listar_ofertas'))


def detalhar_oferta(request, oferta_id):
    usuario = obterUsuario(request)
   
    oferta = OfertaCulto.objects.get(id=oferta_id)
    context = {
        'usuario': usuario,
        'igreja': usuario.igreja,
        'oferta': oferta
    }
    return render(request, 'financas/entradas/ofertas/detalhar.html', context)


def editar_oferta(request, oferta_id):
    usuario = obterUsuario(request)
    oferta = OfertaCulto.objects.get(id=oferta_id)

    if request.method == "POST":
        form = OfertaForm(request.POST, instance=oferta)
        
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('detalhar_oferta', args=[oferta.id]))
    else:
        form = OfertaForm(instance=oferta)

    context = {
        'usuario': usuario,
        'igreja': usuario.igreja,
        'form' : form,
    }
    return render(request, 'financas/entradas/ofertas/editar.html', context)



####################### - - - - - - RELATÓRIO MENSAL - - - - - -  ############################

def criar_primeiro_relatorio_mensal(igreja, entrada):
    ############ obtendo a data que contém o último dia do mês
    data_atual = datetime.now()

    # Obtém o último dia do mês
    ultimo_dia = calendar.monthrange(data_atual.year, data_atual.month)[1]

    # Cria a data do último dia do mês
    data_ultimo_dia = datetime(data_atual.year, data_atual.month, ultimo_dia)

    # Formata a data no formato "dd/mm/aaaa"
    data_fim = data_ultimo_dia.strftime("%Y-%m-%d")
    
    data_criacao = datetime.now()
    data_criacao = data_criacao.strftime("%Y-%m-%d")
    relatorio_mensal = RelatorioMensal(igreja=igreja, entradas=entrada, data_inicio=data_criacao, data_fim=data_fim)
    relatorio_mensal.save()


def criar_novo_relatorio_mensal(request):
    user = obterUsuario(request)
    igreja = Igreja.objects.get(nome=user.igreja.nome)
    entrada = Entrada.objects.get(igreja=user.igreja)
    ############ obtendo a data que contém o último dia do mês
    data_atual = datetime.now()

    # Obtém o último dia do mês
    ultimo_dia = calendar.monthrange(data_atual.year, data_atual.month)[1]

    # Cria a data do último dia do mês
    data_ultimo_dia = datetime(data_atual.year, data_atual.month, ultimo_dia)

    # Formata a data no formato "dd/mm/aaaa"
    data_fim = data_ultimo_dia.strftime("%Y-%m-%d")
    
    data_criacao = datetime.now()
    data_criacao = data_criacao.strftime("%Y-%m-%d")
    relatorio_mensal = RelatorioMensal(igreja=igreja, data_inicio=data_criacao, data_fim=data_fim)
    relatorio_mensal.save()

    return HttpResponseRedirect(reverse('listar_relatorios_gerais'))


def listar_relatorios_mensais(request):
    usuario = obterUsuario(request)
    if usuario.funcao == 'Tesoureiro':
        relatorios_mensais = RelatorioMensal.objects.filter(igreja=usuario.igreja)
    else:
        relatorios_mensais = RelatorioMensal.objects.exclude(igreja=usuario.igreja)
    
    relatorios_particulares = RelatorioMensal.objects.filter(igreja=usuario.igreja)

    context = {
        'relatorios': relatorios_mensais,
        'relatorios_tesoureiro': relatorios_particulares,
        'usuario': usuario,
    }
    return render(request, 'financas/relatorios/mensal/listar.html', context)


def excluir_relatorio_mensal(request, relatorio_id):
    relatorio_mensal = RelatorioMensal.objects.get(id=relatorio_id)
    relatorio_mensal.delete()

    return HttpResponseRedirect(reverse('listar_relatorios_mensais'))


def detalhar_relatorio_mensal(request, relatorio_id):
   
    relatorio_mensal = RelatorioMensal.objects.get(id=relatorio_id)
    context = {
        'relatorio_mensal': relatorio_mensal
    }
    return render(request, 'financas/relatorios/mensal/detalhar.html', context)


def finalizar_relatorio_mensal(request, relatorio_id):
    relatorio = RelatorioMensal.objects.get(id=relatorio_id)
    relatorio.status = 'finalizado'
    relatorio.save()
    criar_novo_relatorio_mensal(request)
    return HttpResponseRedirect(reverse('listar_relatorios_mensais'))

####################### - - - RELATÓRIO GERAL - - - ######################

def criar_primeiro_relatorio_geral(tesoureiro):
    ############ obtendo a data que contém o último dia do mês
    data_atual = datetime.now()

    # Obtém o último dia do mês
    ultimo_dia = calendar.monthrange(data_atual.year, data_atual.month)[1]

    # Cria a data do último dia do mês
    data_ultimo_dia = datetime(data_atual.year, data_atual.month, ultimo_dia)

    # Formata a data no formato "dd/mm/aaaa"
    data_fim = data_ultimo_dia.strftime("%Y-%m-%d")
    
    print('chamou a funcao')
    data_criacao = datetime.now()
    data_criacao = data_criacao.strftime("%Y-%m-%d")
    relatorio_geral = RelatorioGeral(tesoureiro_sede=tesoureiro, data_inicio=data_criacao,  data_fim=data_fim)
    relatorio_geral.save()
    print('criou o relatorio')


def criar_novo_relatorio_geral(request):
    user = obterUsuario(request)
    entrada = Entrada.objects.get(igreja=user.igreja)

    ############ obtendo a data que contém o último dia do mês
    data_atual = datetime.now()

    # Obtém o último dia do mês
    ultimo_dia = calendar.monthrange(data_atual.year, data_atual.month)[1]

    # Cria a data do último dia do mês
    data_ultimo_dia = datetime(data_atual.year, data_atual.month, ultimo_dia)

    # Formata a data no formato "dd/mm/aaaa"
    data_fim = data_ultimo_dia.strftime("%Y-%m-%d")
    
    print('chamou a funcao')
    data_criacao = datetime.now()
    data_criacao = data_criacao.strftime("%Y-%m-%d")
    relatorio_geral = RelatorioGeral(tesoureiro_sede=user, data_inicio=data_criacao,  data_fim=data_fim)
    relatorio_geral.save()
    print('criou o relatorio')

    return HttpResponseRedirect(reverse('listar_relatorios_gerais'))


def listar_relatorios_gerais(request):
    usuario = obterUsuario(request)
    relatorios_gerais = RelatorioGeral.objects.filter(tesoureiro_sede=usuario)
    context = {
        'relatorios': relatorios_gerais
    }
    return render(request, 'financas/relatorios/geral/listar.html', context)


def excluir_relatorio_geral(request, relatorio_id):
    relatorio_geral = RelatorioGeral.objects.get(id=relatorio_id)
    relatorio_geral.delete()

    return HttpResponseRedirect(reverse('listar_relatorios_gerais'))


def detalhar_relatorio_geral(request, relatorio_id):

    relatorio_geral = RelatorioGeral.objects.get(id=relatorio_id)

    if request.method == "POST":
        form = RelatorioGeralForm(request.POST, instance=relatorio_geral)
        
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('detalhar_relatorio_geral', args=[relatorio_geral.id]))
    else:
        form = RelatorioGeralForm(instance=relatorio_geral)
   
    
    context = {
        'relatorio_geral': relatorio_geral,
        'form' : form,
    }
    return render(request, 'financas/relatorios/geral/detalhar.html', context)

   

def finalizar_relatorio_geral(request, relatorio_id):
    relatorio = RelatorioGeral.objects.get(id=relatorio_id)
    relatorio.status = 'finalizado'
    relatorio.save()

    criar_novo_relatorio_geral(request)
    return HttpResponseRedirect(reverse('listar_relatorios_gerais'))


############################ Gerar PDF  #######################
@login_required
@permission_required('accounts.tesoureiro')
def gerar_relatorio(request):
    data_atual = datetime.now()
    data_atual = data_atual.strftime("%d/%m/%Y às %H:%M")
    tesoureiro = obterUsuario(request)
    print(tesoureiro.igreja)
    naoBaixar = 0
    buf = io.BytesIO()
    c= canvas.Canvas(buf, pagesize=letter, bottomup=0)
    textob = c.beginText()
    textob.setTextOrigin(inch, inch)
    textob.setFont("Arial", 14)
    
    saidas = Saida.objects.all()

    lines = []
    lines.append(str(tesoureiro.igreja))
    lines.append(" ")
    lines.append("Relatório de Saídas - Mês e ano")
    lines.append(" ")
    lines.append(" ")
    lines.append(" ")
    lines.append("       Data                         Valor(R$)                        Descrição")
    lines.append(" ")

  
       
    if saidas:
        total = 0
        for saida in saidas:
                lines.append(str(saida.data) + '                      ' + str(f'{saida.valor:,.2f}') + '                     ' + str(saida.descricao))
                lines.append("______________________________________________________________")
                lines.append(" ")
                total = total + saida.valor
        naoBaixar = naoBaixar+1

    lines.append(" ")
    lines.append(f'Total: R${total:,.2f}')
    lines.append(" ")
    lines.append(" ")
    lines.append("Emitido em: " + str(data_atual))

    

           
    for line in lines:
        textob.textLine(line)

    c.drawText(textob)
    c.showPage()
    c.save()
    buf.seek(0)
    return FileResponse(buf, as_attachment=True, filename= 'lista.pdf')


