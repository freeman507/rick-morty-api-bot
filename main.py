from random import randrange  # biblioteca para gerar numeros aleatórios

import requests  # biblioteca para fazer chamadas http
from ramapi import ramapi  # biblioteca da API do rick and morty
from telegram import Update, ReplyKeyboardMarkup, ParseMode  # biblioteca da telegram API
from telegram.ext import ConversationHandler, Updater, CommandHandler, CallbackContext, MessageHandler, \
    Filters  # biblioteca da telegram API

users = []  # base de dados local e temporária para armazenar usuários.


def iniciar_handler(update: Update, context: CallbackContext):
    '''
    Handler disparado quando em resposta ao comando /iniciar
    Dá mensagem de boas vindas, faz uma pergunta e depois
    passa o bot para o estado 1 do fluxo conversasional
    '''
    update.message.reply_text("Welcome! To Rick and Morty Quiz Bot!")  # Imprime mensagem de boas vindas no chat
    pergunta_handler(update, context)  # Faz a primeira pergunta
    return 1  # Deixa o bot no estado 1 do fluxo conversasional


def sair_handler(update: Update, context: CallbackContext):
    '''
    Método para sair do bot, também imprime todos os scores.
    '''
    update.message.reply_text("SCORES:")  # imprime "SCORES:" no chat
    text = ""  # variavel para armazenar a mensagem dos scores
    for user in users:  # percorre todos os usuários cadastrados no bot
        text = text + str(user["score"]) + " >>> " + user["name"] + "\n"  # cria a mensagem do score do usuário
    update.message.reply_text(text)  # imprime todos os scores no chat
    update.message.reply_text("Thank you to use Rick and Morty Quiz Bot!")  # imprime mensagem de saida
    return ConversationHandler.END  # finaliza fluxo conversasional


def load_description(character):
    '''
    Método que cria a descrição do personagem com base no template do arquivo
    description.md localizado na pasta raiz deste projeto
    '''
    with open("description.md") as file:  # abre o arquivo para leitura
        # atribui o conteudo do arquivo a variavel description
        description = file.read()
        # substitui a palavra coringa $name pelo nome do personagem
        description = description.replace("$name", character["name"])
        # substitui a palavra coringa $species pela espécie do personagem
        description = description.replace("$species", character["species"])
        # substitui a palavra coringa $type pelo tipo do personagem
        description = description.replace("$type", character["type"])
        # substitui a palavra coringa $gender pelo gênero do personagem
        description = description.replace("$gender", character["gender"])
    return description  # retorna a descrição pronta do personagem


def send_description(context, character, update):
    '''
    Método que imprime a descrição do personagem no formato markdown
    '''
    description = load_description(character)  # prepara a descrição do personagem no formato MARKDOWN
    update.message.reply_text(text=description, parse_mode=ParseMode.MARKDOWN)  # imprime a descrição do personagem


def pergunta_handler(update: Update, context: CallbackContext):
    '''
    Método que imprime a foto e a descrição do personagem,
    faz a pergunta e imprime os botões
    '''
    character = ramapi.Character.get(randrange(826))  # Busca um personagem aleatório na API do rick and morty
    bind_character_to_user(character, update)  # Vincula o personagem ao usuário
    response = requests.get(character["image"])  # busca a imagem do personagem na internet
    send_photo(context, response.content, update)  # imprime a foto do personagem
    send_description(context, character, update)  # imprime a descrição do personagem
    send_question(update)  # imprime a pergunta com os botões
    return 1  # Retorna ao estado 1 do fluxo conversasional


def bind_character_to_user(character, update):
    '''
    Método que cadastra um usuário ou vincula um novo personagem ao usuário
    '''
    user = get_user(update.effective_user.id)  # Busca o usuário cadastrado pelo id
    if not user:  # verifica se o usuário está cadastrado, senão cadastra um novo
        add_user(update.effective_user, character)  # cadastra um novo usuário
    else:
        user["character"] = character  # vincula um novo personagem ao usuário


def send_question(update):
    '''
    Método que imprime a pergunta e os botões no chat do bot
    '''
    buttons = ReplyKeyboardMarkup(  # cria os botões com as 3 opções de resposta
        [["Alive", "Dead", "Unknown"]],
        one_time_keyboard=True,
        resize_keyboard=True
    )
    update.message.reply_text(  # envia a pergunta e os botões para o chat do bot
        "What is the status of this character?",
        reply_markup=buttons,
        parse_mode=ParseMode.MARKDOWN_V2,
    )


def send_photo(context, photo, update):
    '''
    Método que imprime a foto no chat
    '''
    context.bot.send_photo(chat_id=update.message.chat_id, photo=photo)


def answers_handler(update: Update, context: CallbackContext):
    '''
    Método disparado quando o usuário clica em uma resposta
    Retorna para o estado 1 do bot
    '''
    effective_user = update.effective_user  # busca o usuário do telegram
    user = get_user(effective_user["id"])  # busca o usuário cadastrado
    if user["character"]["status"] == update.message.text:  # verifica se a resposta do usuário está certa
        update.message.reply_text("Right!")  # imprime que a resposta está certa
        user["score"] = user["score"] + 10  # atualiza o score do usuário
    else:
        update.message.reply_text("Wrong")  # imprime que a resposta está errada
        user["score"] = user["score"] - 10 if user["score"] > 0 else 0  # atualiza o score do usuário
    return pergunta_handler(update, context)  # faz outra pergunta ao usuário


def add_user(effective_user, character):
    '''
    Método que cadastra um novo usuário do telegram no bot
    '''
    user = {
        "id": effective_user.id,  # id do usuario do telegram
        "name": effective_user.full_name,  # nome completo do usuario do telegram
        "score": 0,  # score inicial do usuario
        "character": character  # vincula um personagem ao usuário
    }
    users.append(user)  # adiciona o novo usuário ao bot
    return user  # retorna o novo usuário cadastrado


def get_user(id):
    '''
    Busca um usuário cadastrado pelo id do usuário do telegram,
    retorna None quando o usuário ainda não foi cadastrado
    '''
    for user in users:
        if user["id"] == id:
            return user
    return None


fluxo_conversasional = ConversationHandler(  # Cria Objeto de conversasão
    entry_points=[  # Parametro que determina as ações de entrada
        CommandHandler("iniciar", iniciar_handler), # Objeto que trata o comando /iniciar
        CommandHandler("start", iniciar_handler)  # Objeto que trata o comando /iniciar
    ],
    states={  # Parametro que indica os estados da conversa
        1: [  # estado 1
            MessageHandler(Filters.regex("^(Alive)$"), answers_handler),  # Objeto que trata a resposta "Alive"
            MessageHandler(Filters.regex("^(Dead)$"), answers_handler),  # Objeto que trata a resposta "Dead"
            MessageHandler(Filters.regex("^(Unknown)$"), answers_handler),  # Objeto que trata a resposta "Unknown"
        ]
    },
    fallbacks=[  # Parametro que trata os pontos de saida do bot
        CommandHandler("sair", sair_handler)  # Objeto que trata o comando /sair
    ]
)

if __name__ == '__main__':
    token = ''  # Token obtido pelo BotFather
    updater = Updater(token, use_context=True)  # Cria bot
    updater.dispatcher.add_handler(fluxo_conversasional)  # Adiciona Comportamento ao bot
    updater.start_polling()  # Inicia Bot
