from flask import Flask, request, jsonify
import logging
import os
from dotenv import load_dotenv

from bot.ai_bot import AIBot
from services.waha import Waha

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

app = Flask(__name__)

# Configuração do logger
logging.basicConfig(level=logging.DEBUG)

# Verificar se as variáveis de ambiente estão carregadas
logging.debug("GROQ_API_KEY: %s", os.getenv('GROQ_API_KEY'))
logging.debug("HUGGINGFACE_API_KEY: %s", os.getenv('HUGGINGFACE_API_KEY'))

@app.route('/')
def index():
    return "Servidor Flask está rodando!"

@app.route('/chatbot/webhook/', methods=['POST'])
def webhook():
    try:
        data = request.json
        logging.debug("Dados recebidos: %s", data)
        
        payload = data.get('payload', {})
        chat_id = payload.get('from')
        received_message = payload.get('body')
        
        if not chat_id or not received_message:
            logging.error("Dados inválidos recebidos: %s", data)
            return jsonify({'status': 'error', 'message': 'Dados inválidos recebidos.'}), 400

        is_group = '@g.us' in chat_id

        if is_group:
            logging.debug("Mensagem de grupo ignorada.")
            return jsonify({'status': 'success', 'message': 'Mensagem de grupo ignorada.'}), 200

        waha = Waha()
        ai_bot = AIBot()
        waha.start_typing(chat_id=chat_id)
        history_messages = waha.get_history_messages(chat_id=chat_id, limit=10)
        response_message = ai_bot.invoke(history_messages=history_messages, question=received_message)
        logging.debug("Resposta do bot: %s", response_message)
        waha.send_message(chat_id=chat_id, message=response_message)
        waha.stop_typing(chat_id=chat_id)

        return jsonify({'status': 'success', 'message': 'Mensagem processada com sucesso.'}), 200
    except KeyError as e:
        logging.error("Chave ausente no payload: %s", e)
        return jsonify({'status': 'error', 'message': f'Chave ausente no payload: {e}'}), 400
    except Exception as e:
        logging.error("Erro ao processar a solicitação: %s", e, exc_info=True)
        return jsonify({'status': 'error', 'message': 'Erro interno do servidor.'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)