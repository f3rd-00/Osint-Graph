# Backend do OutraSec

Backend local simples em Python (Flask) que dá suporte às buscas de:
CEP → mapa do endereço, IP → geolocalização aproximada, e Telegram → nome/foto (opcional).

## 1. Instalar

```bash
cd backend
pip install -r requirements.txt
```

## 2. Rodar

```bash
python app.py
```

Isso deixa o servidor rodando em `http://localhost:5000`. Deixe essa janela aberta
enquanto usa o `outrasec.html` — é ele quem conversa com esse backend.

> Dica: rode `python main.py` na pasta raiz do projeto para subir o backend
> e abrir o `outrasec.html` automaticamente, sem precisar fazer isso na mão.

## 3. (Opcional) Configurar o Telegram

Sem isso, o botão "Telegram" no menu do nó tipo Telefone vai avisar que não está
configurado. Para habilitar:

1. Entre em https://my.telegram.org com seu número de telefone.
2. Vá em "API development tools" e crie um app (qualquer nome serve).
3. Copie o `api_id` e o `api_hash`.
4. Rode (na pasta `backend`):
   ```bash
   set TELEGRAM_API_ID=SEU_API_ID
   set TELEGRAM_API_HASH=SEU_API_HASH
   python telegram_login.py
   ```
   Vai pedir o código que chega no seu Telegram. Isso cria `telegram.session`.
5. Reinicie o `app.py` com as mesmas variáveis de ambiente definidas (ou deixe
   fixas no começo do `telegram_lookup.py`, se preferir).

**Limitações do Telegram:** só funciona se o número já estiver no Telegram e a
pessoa permitir ser encontrada pelo telefone (configuração de privacidade dela).
Não abuse — consultar muitos números rápido pode limitar sua conta.

## O que NÃO foi implementado (e por quê)

- **WhatsApp**: não existe API pública para consultar nome/foto de um número
  qualquer. As únicas formas são bibliotecas não-oficiais que exigem logar
  com QR code na sua própria conta e só funcionam com contatos que já
  trocaram mensagem com você. O botão existe na interface só para avisar disso.
- **Foto real da fachada (Street View)**: exigiria a API paga do Google Maps
  Platform (chave + cartão de crédito cadastrado). O que o backend gera no
  lugar é uma imagem de mapa/satélite aproximada, de graça, sem chave.
