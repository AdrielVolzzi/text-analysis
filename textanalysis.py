import streamlit as st
from nltk.corpus import stopwords
from nltk import word_tokenize, download
from nltk.util import ngrams
from wordcloud import WordCloud
import pdfplumber
from docx import Document
from collections import Counter
import matplotlib.pyplot as plt
import requests
from bs4 import BeautifulSoup
nltk.download('punkt')
nltk.download('stopwords')

def processar_texto(texto, top_n=20):
    # Tokenização e remoção de stopwords
    stop_words = set(stopwords.words('portuguese'))
    palavras = [palavra for palavra in word_tokenize(texto.lower()) if palavra.isalpha() and palavra not in stop_words]

    # Frequência das palavras
    frequencia = Counter(palavras)
    mais_frequentes = frequencia.most_common(top_n)

    # Nuvem de palavras
    nuvem = WordCloud(width=800, height=400, background_color='white').generate(" ".join(palavras))

    return mais_frequentes, nuvem

# Função para extrair texto de diferentes tipos de arquivo
def extrair_texto(arquivo):
    if arquivo.type == "application/pdf":
        texto = ""
        with pdfplumber.open(arquivo) as pdf:
            for pagina in pdf.pages:
                texto += pagina.extract_text()
    elif arquivo.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = Document(arquivo)
        texto = "\n".join([paragrafo.text for paragrafo in doc.paragraphs])
    else:  # Tratamento para arquivos de texto simples
        texto = str(arquivo.read(), "utf-8")
    return texto

def extrair_texto_site(url):
    try:
        resposta = requests.get(url)
        resposta.raise_for_status()  # Verifica se a requisição foi bem-sucedida
        soup = BeautifulSoup(resposta.text, 'html.parser')

        # Extrai o texto de todos os elementos <p> e concatena
        paragrafos = soup.find_all('p')
        texto = ' '.join(paragrafo.get_text() for paragrafo in paragrafos)
        return texto
    except requests.RequestException as e:
        st.error(f"Erro ao acessar o site: {e}")
        return ""

def gerar_ngramas(texto, n=2, top_n=20):
    stop_words = set(stopwords.words('portuguese'))
    palavras = [palavra for palavra in word_tokenize(texto.lower()) if palavra.isalpha() and not palavra in stop_words]
    n_gramas = ngrams(palavras, n) if n > 1 else [(palavra,) for palavra in palavras]  # Ajuste para incluir unigramas como tuplas
    frequencia = Counter(n_gramas)
    # Converter n-gramas para string para exibição
    mais_frequentes = [(" ".join(grama), freq) for grama, freq in frequencia.most_common(top_n)]
    return mais_frequentes

def distribuicao_comprimento_palavra(texto):
    download('punkt')
    palavras = word_tokenize(texto.lower())
    comprimentos = [len(palavra) for palavra in palavras if palavra.isalpha()]
    frequencia = Counter(comprimentos)
    return frequencia

# Inicialização de variáveis de sessão
if 'pagina' not in st.session_state:
    st.session_state.pagina = 'entrada'

# Página de entrada
if st.session_state.pagina == 'entrada':
    st.title('Análise Estatística de Texto')
    texto_entrada = st.text_area("Insira seu texto aqui:", height=250)
    url_site = st.text_input("Cole a URL do site aqui:")
    arquivo = st.file_uploader("", type=["pdf", "docx", "txt"], help="Anexe um arquivo PDF, DOCX ou TXT")
    analises = st.multiselect("Selecione as análises desejadas:", 
                              ['Nuvem de Palavras', 'Top Palavras', 'Top Bigramas', 'Top Trigramas', 'Top Quadrigramas', 'Distribuição de Comprimento de Palavra'])
    top_n = int(st.number_input("Especifique o Top N para análise (se aplicável):", min_value=1, max_value=100, value=20))
    
    if st.button('Pronto'):
        if arquivo is not None:
            texto_entrada = extrair_texto(arquivo)
            print(1)
            st.session_state.texto = texto_entrada
            st.session_state.analises = analises
            st.session_state.top_n = top_n
            st.session_state.pagina = 'resultados'
            st.rerun()
        elif texto_entrada:
            st.session_state.texto = texto_entrada
            st.session_state.analises = analises
            st.session_state.top_n = top_n
            st.session_state.pagina = 'resultados'
            st.rerun()
        elif url_site is not None:
            texto_entrada = extrair_texto_site(url_site)
            st.session_state.texto = texto_entrada
            st.session_state.analises = analises
            st.session_state.top_n = top_n
            st.session_state.pagina = 'resultados'
            st.rerun()
            print(2)
        else:
            st.warning("Por favor, insira um texto ou anexe um arquivo.")

# Página de resultados
elif st.session_state.pagina == 'resultados':
    st.title('Resultados da Análise')
    if 'Nuvem de Palavras' in st.session_state.analises:
        mais_frequentes, nuvem = processar_texto(st.session_state.texto, st.session_state.top_n)
        st.subheader("Nuvem de Palavras")
        fig, ax = plt.subplots()
        ax.imshow(nuvem, interpolation='bilinear')
        ax.axis('off')
        st.pyplot(fig)

    opcoes_para_n = {
        'Top Palavras': 1,
        'Top Bigramas': 2,
        'Top Trigramas': 3,
        'Top Quadrigramas': 4
    }

    for analise in st.session_state.analises:
        if analise in opcoes_para_n:
            n = opcoes_para_n[analise]
            resultados = gerar_ngramas(st.session_state.texto, n, st.session_state.top_n)
            st.subheader(f"{analise} ({st.session_state.top_n})")
            for resultado in resultados:
                st.text(f"{resultado[0]}: {resultado[1]}")

    if 'Distribuição de Comprimento de Palavra' in st.session_state.analises:
        distribuicao = distribuicao_comprimento_palavra(st.session_state.texto)
        st.subheader("Distribuição de Frequência do Comprimento das Palavras")
        fig, ax = plt.subplots()
        ax.bar(distribuicao.keys(), distribuicao.values())
        ax.set_xlabel('Comprimento da Palavra')
        ax.set_ylabel('Frequência')
        st.pyplot(fig)


    if st.button('Voltar'):
        st.session_state.pagina = 'entrada'
        st.experimental_rerun() 