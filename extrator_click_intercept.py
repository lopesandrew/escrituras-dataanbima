"""
Extrator de Escrituras ANBIMA - Click + Network Intercept
Aguarda página carregar, clica nos botões Baixar e intercepta URLs
"""

from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import csv
import time
from datetime import datetime
import os


def criar_driver():
    """Cria driver do Chrome com interceptação"""
    chrome_options = Options()
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])

    seleniumwire_options = {
        'disable_encoding': True
    }

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(
        service=service,
        options=chrome_options,
        seleniumwire_options=seleniumwire_options
    )
    return driver


def ler_ativos_arquivo(nome_arquivo='ativos.txt'):
    """Lê lista de ativos de um arquivo"""
    if not os.path.exists(nome_arquivo):
        print(f"[ERRO] Arquivo '{nome_arquivo}' nao encontrado!")
        return []

    with open(nome_arquivo, 'r', encoding='utf-8') as f:
        ativos = [linha.strip().upper() for linha in f if linha.strip()]

    return ativos


def buscar_escrituras(driver, ativo, timeout=60):
    """Busca escrituras clicando em botões e interceptando rede"""
    url = f"https://data.anbima.com.br/debentures/{ativo}/documentos"

    print(f"\n{'='*60}")
    print(f"[BUSCANDO] Ativo: {ativo}")
    print(f"[URL] {url}")
    print(f"{'='*60}")

    resultado = {
        'ativo': ativo,
        'link_original': '',
        'link_recente': '',
        'status': ''
    }

    try:
        # Limpa requests anteriores
        del driver.requests

        # Acessa a página
        driver.get(url)

        wait = WebDriverWait(driver, timeout)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # Fecha popup de cookies
        try:
            print("[INFO] Verificando popup de cookies...", flush=True)
            wait_cookie = WebDriverWait(driver, 5)
            cookie_link = wait_cookie.until(EC.element_to_be_clickable((
                By.XPATH,
                "//a[contains(@href, 'aceito-as-regras') or contains(text(), 'Prosseguir')]"
            )))
            cookie_link.click()
            print("[OK] Popup de cookies fechado", flush=True)
            time.sleep(2)
        except:
            print("[INFO] Sem popup de cookies", flush=True)

        # Aguarda JavaScript carregar
        print("[INFO] Aguardando JavaScript carregar (20s)...", flush=True)
        time.sleep(20)

        # Busca botões Baixar
        print("[INFO] Buscando botoes Baixar...", flush=True)
        baixar_buttons = driver.find_elements(By.XPATH, "//a[contains(text(), 'Baixar')]")
        print(f"[INFO] Encontrados {len(baixar_buttons)} botoes", flush=True)

        escrituras_encontradas = []

        # Clica em cada botão e verifica requests
        for i, button in enumerate(baixar_buttons, 1):
            try:
                print(f"[INFO] Clicando no botao {i}...", flush=True)

                # Limpa requests before
                del driver.requests

                # Clica no botão
                driver.execute_script("arguments[0].click();", button)

                # Aguarda um pouco para possível request
                time.sleep(2)

                # Analisa requests após o clique
                for request in driver.requests:
                    try:
                        url_req = request.url

                        # Procura por URLs S3 com PDF
                        if 's3.amazonaws.com' in url_req.lower() and '.pdf' in url_req.lower():
                            termos = ['escritura', 'deed', 'indenture']
                            if any(termo in url_req.lower() for termo in termos):
                                escrituras_encontradas.append(url_req)
                                print(f"[OK] S3 capturado apos clique {i}: {url_req[:80]}...", flush=True)
                    except:
                        continue

            except Exception as e:
                print(f"[AVISO] Erro ao clicar botao {i}: {str(e)[:50]}", flush=True)

        if escrituras_encontradas:
            # Remove duplicatas
            links_unicos = list(set(escrituras_encontradas))
            links_ord = sorted(links_unicos)

            resultado['link_original'] = links_ord[0]
            resultado['link_recente'] = links_ord[-1] if len(links_ord) > 1 else links_ord[0]
            resultado['status'] = f"{len(links_unicos)} encontrada(s)"
            print(f"[SUCESSO] {len(links_unicos)} escritura(s) encontrada(s)", flush=True)
        else:
            resultado['status'] = "Nenhuma escritura"
            print("[AVISO] Nenhuma escritura encontrada apos cliques", flush=True)

    except Exception as e:
        resultado['status'] = f"Erro: {str(e)[:50]}"
        print(f"[ERRO] {e}", flush=True)

    return resultado


def salvar_csv(resultados):
    """Salva em CSV"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    arquivo = f'escrituras_{timestamp}.csv'

    with open(arquivo, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(['Ativo', 'Link Original', 'Link Recente', 'Status'])

        for r in resultados:
            writer.writerow([
                r['ativo'],
                r['link_original'],
                r['link_recente'],
                r['status']
            ])

    print(f"\n[OK] Salvo: {arquivo}")
    return arquivo


def main():
    """Função principal"""
    print("="*60)
    print("EXTRATOR DE ESCRITURAS - ANBIMA")
    print("   (Click + Network Intercept)")
    print("="*60)

    # Lê ativos do arquivo
    arquivo_entrada = 'ativos_remaining.txt'
    ativos = ler_ativos_arquivo(arquivo_entrada)

    if not ativos:
        return

    print(f"\n[OK] {len(ativos)} ativo(s) carregado(s)")
    print(f"[INFO] Ativos: {', '.join(ativos[:5])}{'...' if len(ativos) > 5 else ''}")

    print("\n[INICIANDO] Chrome com interceptacao...")
    driver = None

    try:
        driver = criar_driver()
        print("[OK] Chrome iniciado com sucesso")

        resultados = []
        erros_consecutivos = 0

        for i, ativo in enumerate(ativos, 1):
            print(f"\n{'='*60}")
            print(f"[PROGRESSO] Processando {i}/{len(ativos)}")
            print(f"{'='*60}")

            try:
                resultado = buscar_escrituras(driver, ativo)
                resultados.append(resultado)
                erros_consecutivos = 0
            except Exception as e:
                print(f"[ERRO CRITICO] Falha ao processar {ativo}: {e}")
                resultados.append({
                    'ativo': ativo,
                    'link_original': '',
                    'link_recente': '',
                    'status': f'Erro critico'
                })
                erros_consecutivos += 1

                if erros_consecutivos >= 3:
                    print("[AVISO] Muitos erros consecutivos. Recriando navegador...")
                    try:
                        driver.quit()
                    except:
                        pass
                    driver = criar_driver()
                    erros_consecutivos = 0

            # Pausa entre requisições
            if i < len(ativos):
                time.sleep(3)

        # Salva resultados
        print("\n" + "="*60)
        print("[INFO] Salvando resultados...")
        salvar_csv(resultados)

        # Resumo final
        print("\n" + "="*60)
        print("RESUMO FINAL")
        print("="*60)
        total = len(resultados)
        sucesso = sum(1 for r in resultados if 'encontrada' in r['status'])
        sem_docs = sum(1 for r in resultados if r['status'] == 'Nenhuma escritura')
        erros = total - sucesso - sem_docs

        print(f"[OK] Processados: {total} ativos")
        print(f"[OK] Com escrituras: {sucesso}")
        print(f"[AVISO] Sem documentos: {sem_docs}")
        print(f"[ERRO] Erros: {erros}")

    except Exception as e:
        print(f"\n[ERRO FATAL] {e}")

    finally:
        if driver:
            try:
                driver.quit()
                print("\n[OK] Navegador encerrado")
            except:
                pass
        print("[OK] Script finalizado")


if __name__ == "__main__":
    main()
