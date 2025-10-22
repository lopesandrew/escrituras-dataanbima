"""
Módulo de Download de PDFs - Escrituras ANBIMA
Baixa automaticamente os PDFs das escrituras a partir do CSV gerado
"""

import csv
import os
import requests
import time
from urllib.parse import unquote
from datetime import datetime


def extrair_codigo_empresa(ativo):
    """Extrai o código da empresa dos primeiros 4 caracteres do ativo"""
    return ativo[:4].upper()


def extrair_nome_arquivo(url):
    """Extrai o nome do arquivo da URL S3 e faz decode"""
    nome = url.split('/')[-1]
    return unquote(nome)


def criar_pasta(caminho):
    """Cria uma pasta se ela não existir"""
    if not os.path.exists(caminho):
        os.makedirs(caminho)
        print(f"[INFO] Pasta criada: {caminho}")


def arquivo_existe(caminho):
    """Verifica se o arquivo já existe"""
    return os.path.exists(caminho) and os.path.getsize(caminho) > 0


def baixar_pdf(url, caminho_destino, max_tentativas=3):
    """
    Baixa um PDF da URL S3 para o caminho de destino
    Retorna True se sucesso, False se falhar
    """
    for tentativa in range(1, max_tentativas + 1):
        try:
            print(f"[INFO] Baixando ({tentativa}/{max_tentativas}): {os.path.basename(caminho_destino)}", flush=True)

            response = requests.get(url, timeout=30, stream=True)
            response.raise_for_status()

            # Baixa em chunks para mostrar progresso
            total_size = int(response.headers.get('content-length', 0))

            with open(caminho_destino, 'wb') as f:
                if total_size == 0:
                    f.write(response.content)
                else:
                    downloaded = 0
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)

            tamanho_mb = os.path.getsize(caminho_destino) / (1024 * 1024)
            print(f"[OK] Download concluido: {tamanho_mb:.2f} MB", flush=True)
            return True

        except requests.exceptions.RequestException as e:
            print(f"[AVISO] Tentativa {tentativa} falhou: {str(e)[:80]}", flush=True)
            if tentativa < max_tentativas:
                time.sleep(2)
            else:
                print(f"[ERRO] Falha após {max_tentativas} tentativas", flush=True)
                return False
        except Exception as e:
            print(f"[ERRO] Erro inesperado: {str(e)[:80]}", flush=True)
            return False


def coletar_links_unicos(csv_path):
    """
    Lê o CSV e coleta todos os links únicos por ativo
    Retorna dict: {ativo: [lista de URLs únicas]}
    """
    links_por_ativo = {}

    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter=';')

        for row in reader:
            ativo = row['Ativo']
            link_original = row.get('Link Original', '').strip()
            link_recente = row.get('Link Recente', '').strip()
            status = row.get('Status', '')

            # Ignora ativos sem escrituras
            if 'Nenhuma escritura' in status or not link_original:
                continue

            # Coleta links únicos
            links = set()
            if link_original:
                links.add(link_original)
            if link_recente and link_recente != link_original:
                links.add(link_recente)

            if links:
                links_por_ativo[ativo] = list(links)

    return links_por_ativo


def main():
    """Função principal"""
    print("="*60)
    print("DOWNLOADER DE PDFs - ESCRITURAS ANBIMA")
    print("="*60)

    # Configura caminhos
    csv_path = 'escrituras_FINAL_20251021_155810.csv'
    pasta_base = 'escrituras'

    if not os.path.exists(csv_path):
        print(f"[ERRO] Arquivo CSV não encontrado: {csv_path}")
        return

    print(f"\n[INFO] Lendo CSV: {csv_path}")
    links_por_ativo = coletar_links_unicos(csv_path)

    total_ativos = len(links_por_ativo)
    total_pdfs = sum(len(links) for links in links_por_ativo.values())

    print(f"[OK] {total_ativos} ativos com escrituras")
    print(f"[OK] {total_pdfs} PDFs para baixar")

    # Cria pasta base
    criar_pasta(pasta_base)

    # Estatísticas
    downloads_sucesso = 0
    downloads_pulados = 0
    downloads_falha = 0

    # Processa cada ativo
    for i, (ativo, links) in enumerate(links_por_ativo.items(), 1):
        print(f"\n{'='*60}")
        print(f"[{i}/{total_ativos}] Processando: {ativo}")
        print(f"{'='*60}")

        # Extrai código da empresa e cria subpasta
        empresa = extrair_codigo_empresa(ativo)
        pasta_empresa = os.path.join(pasta_base, empresa)
        criar_pasta(pasta_empresa)

        print(f"[INFO] Pasta: {pasta_empresa}")
        print(f"[INFO] {len(links)} PDF(s) a baixar")

        # Baixa cada PDF
        for j, url in enumerate(links, 1):
            nome_arquivo = extrair_nome_arquivo(url)
            caminho_destino = os.path.join(pasta_empresa, nome_arquivo)

            print(f"\n[{j}/{len(links)}] {nome_arquivo[:60]}...")

            # Verifica se já existe
            if arquivo_existe(caminho_destino):
                tamanho_mb = os.path.getsize(caminho_destino) / (1024 * 1024)
                print(f"[PULADO] Arquivo já existe ({tamanho_mb:.2f} MB)")
                downloads_pulados += 1
                continue

            # Tenta baixar
            if baixar_pdf(url, caminho_destino):
                downloads_sucesso += 1
            else:
                downloads_falha += 1

            # Pequena pausa entre downloads
            time.sleep(0.5)

    # Resumo final
    print("\n" + "="*60)
    print("RESUMO FINAL")
    print("="*60)
    print(f"[OK] Downloads bem-sucedidos: {downloads_sucesso}")
    print(f"[INFO] Arquivos já existentes: {downloads_pulados}")
    print(f"[ERRO] Downloads com falha: {downloads_falha}")
    print(f"[TOTAL] PDFs processados: {downloads_sucesso + downloads_pulados + downloads_falha}")

    if downloads_falha == 0:
        print("\n[SUCESSO] Todos os PDFs foram baixados com sucesso!")
    else:
        print(f"\n[AVISO] {downloads_falha} PDF(s) falharam no download")

    print(f"\n[INFO] Pasta de destino: {os.path.abspath(pasta_base)}")


if __name__ == "__main__":
    main()
