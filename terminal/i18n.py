#!/usr/bin/env python3
"""
Textos do fluxo SSH «entre» em pt-BR e en. O visitante escolhe o idioma na
primeira tela da sessão (ver ``entre_app.choose_language``); a escolha vale
para toda a interação — prompts, mensagens de validação e ecrã final.

``tests/test_i18n_strings.py`` garante que toda chave existe nos dois idiomas
(mesma filosofia de ``tests/test_validation_parity.py`` para as constantes de
validação: duplicação aceitável, drift não).

Apenas biblioteca padrão.
"""

from __future__ import annotations

from typing import Final

DEFAULT_LANG: Final[str] = "pt"
SUPPORTED_LANGS: Final[tuple[str, ...]] = ("pt", "en")

STRINGS: Final[dict[str, dict[str, str]]] = {
    "pt": {
        # --- ecrã de abertura ---
        "ascii_tagline": ".club — um computador para compartilhar",
        "press_any_key": "Aperte qualquer tecla para continuar...",
        "press_enter_hint": "  (tecla Enter para continuar)\n",
        "pause_prompt": "\n[Enter] continuar  ·  [q] sair\n",
        "goodbye_quit": "\nAté logo.\n",
        # --- cabeçalho de cada passo do formulário ---
        "step_header_label": "Dados · passo {step}/{total}",
        "step1_title": "Nome de utilizador Unix desejado",
        "step2_title": "Email de contacto",
        "step3_title": "Onde te encontramos online?",
        "step4_title": "Chave pública SSH",
        "step1_help": (
            "Letras minúsculas, dígitos, _ ou -; começa com letra. "
            "Deixa em branco só se ainda não tiveres escolhido.\n"
        ),
        "step2_help": "Endereço para a equipa te responder sobre este pedido.\n",
        "step3_help": (
            "Links, perfis ou páginas onde aparece o teu trabalho, código ou participação "
            "— por exemplo site, GitHub, Mastodon, itch.io, etc. "
            "Uma sugestão por linha.\n"
        ),
        "step4_help": "Uma única linha, a mesma que irias pôr em authorized_keys. Só a pública.\n",
        "input_marker_write": "» Escreve abaixo e prima Enter:",
        "input_marker_multiline": "» A tua resposta (várias linhas):",
        "input_marker_paste": "» Cola a linha abaixo e prima Enter:",
        "multiline_hint": "(podes usar várias linhas; para terminar, uma linha só com . e Enter)",
        "multiline_size_limit": "(limite de tamanho atingido — campo fechado aqui.)",
        # --- validação ---
        "fix_errors_header": "— Corrige os dados —",
        "back_to_form_hint": "\n[Enter] para voltar ao início do formulário\n",
        # --- confirmação ---
        "confirm_option_confirm": "  [c] confirmar envio",
        "confirm_option_edit": "  [e] editar dados",
        "confirm_option_cancel": "  [x] cancelar e sair",
        "confirm_prompt_label": "Opção: ",
        "confirm_invalid_option": "Opção inválida.",
        # --- fim de sessão ---
        "request_cancelled": "\nPedido cancelado. Até logo.\n\n",
        # --- mensagens de validação (entre_core.py) ---
        "err_username_required": "o nome de utilizador desejado é obrigatório.",
        "err_username_too_long": "nome de utilizador demasiado longo.",
        "err_username_format": (
            "use apenas letras minúsculas, dígitos, _ e -; comece com letra; "
            "entre 2 e 32 caracteres."
        ),
        "err_username_reserved": "esse nome está reservado ou não é permitido.",
        "err_username_taken": "esse nome já existe neste servidor.",
        "err_online_presence_required": (
            "indica sítios ou perfis onde possamos ver o teu trabalho ou o que publicas online "
            "(mínimo {min_len} caracteres). Podes usar várias linhas no passo anterior."
        ),
        "err_online_presence_too_short": (
            "esse campo ainda é curto demais — adiciona um link, perfil ou página onde apareças online."
        ),
        "err_online_presence_too_long": (
            "texto demasiado longo; resume ou escolhe os links mais importantes."
        ),
        "err_online_presence_invalid_chars": "caracteres inválidos no texto.",
        "err_email_required": "o email é obrigatório.",
        "err_email_spaces": "o email não pode ter espaços no início ou fim.",
        "err_email_too_long": "email demasiado longo.",
        "err_email_missing_at": "indica um endereço com @, por exemplo nome@exemplo.org.",
        "err_email_multiple_at": "o email deve ter um único @.",
        "err_email_invalid_format": "formato de email inválido.",
        "err_private_key_pasted": (
            "isto parece uma chave **privada**. Nunca a cole aqui. "
            "Cole apenas a linha da chave **pública** (.pub)."
        ),
        "err_pubkey_required": "a chave pública é obrigatória.",
        "err_pubkey_line_too_long": "linha da chave demasiado longa.",
        "err_pubkey_single_line": "cole uma única linha, sem quebras.",
        "err_pubkey_empty": "chave pública vazia.",
        "err_pubkey_malformed": "formato inválido: esperado tipo, dados base64 e comentário opcional.",
        "err_pubkey_unsupported_type": (
            "tipo de chave não aceite ({key_type!r}). "
            "Exemplos: ssh-ed25519, ecdsa-sha2-nistp256, ssh-rsa."
        ),
        "err_pubkey_invalid_base64": "dados da chave (base64) inválidos.",
        "err_pubkey_rejected_by_sshkeygen": "a chave foi rejeitada pelo ssh-keygen: {err}",
        "err_sshkeygen_no_output": "ssh-keygen não devolveu saída",
        "err_sshkeygen_no_fingerprint": "não foi possível ler o fingerprint: {out!r}",
    },
    "en": {
        # --- opening screen ---
        "ascii_tagline": ".club — a computer worth sharing",
        "press_any_key": "Press any key to continue...",
        "press_enter_hint": "  (press Enter to continue)\n",
        "pause_prompt": "\n[Enter] continue  ·  [q] quit\n",
        "goodbye_quit": "\nSee you soon.\n",
        # --- header for each form step ---
        "step_header_label": "Data · step {step}/{total}",
        "step1_title": "Desired Unix username",
        "step2_title": "Contact email",
        "step3_title": "Where can we find you online?",
        "step4_title": "SSH public key",
        "step1_help": (
            "Lowercase letters, digits, _ or -; must start with a letter. "
            "Leave it blank only if you haven't picked one yet.\n"
        ),
        "step2_help": "Address the team can use to reply about this request.\n",
        "step3_help": (
            "Links, profiles, or pages where your work, code, or activity shows up "
            "— for example a site, GitHub, Mastodon, itch.io, etc. "
            "One suggestion per line.\n"
        ),
        "step4_help": "A single line, the same one you'd put in authorized_keys. Public key only.\n",
        "input_marker_write": "» Type below and press Enter:",
        "input_marker_multiline": "» Your answer (multiple lines):",
        "input_marker_paste": "» Paste the line below and press Enter:",
        "multiline_hint": "(you can use multiple lines; to finish, a line with just . and Enter)",
        "multiline_size_limit": "(size limit reached — field closed here.)",
        # --- validation ---
        "fix_errors_header": "— Fix the data —",
        "back_to_form_hint": "\n[Enter] to go back to the start of the form\n",
        # --- confirmation ---
        "confirm_option_confirm": "  [c] confirm submission",
        "confirm_option_edit": "  [e] edit data",
        "confirm_option_cancel": "  [x] cancel and quit",
        "confirm_prompt_label": "Option: ",
        "confirm_invalid_option": "Invalid option.",
        # --- session end ---
        "request_cancelled": "\nRequest cancelled. See you soon.\n\n",
        # --- validation messages (entre_core.py) ---
        "err_username_required": "the desired username is required.",
        "err_username_too_long": "username is too long.",
        "err_username_format": (
            "use only lowercase letters, digits, _ and -; start with a letter; "
            "between 2 and 32 characters."
        ),
        "err_username_reserved": "that name is reserved or not allowed.",
        "err_username_taken": "that username already exists on this server.",
        "err_online_presence_required": (
            "tell us about sites or profiles where we can see your work or what you publish online "
            "(minimum {min_len} characters). You can use multiple lines in the previous step."
        ),
        "err_online_presence_too_short": (
            "that field is still too short — add a link, profile, or page where you show up."
        ),
        "err_online_presence_too_long": (
            "text is too long; summarize it or pick the most important links."
        ),
        "err_online_presence_invalid_chars": "invalid characters in the text.",
        "err_email_required": "email is required.",
        "err_email_spaces": "email can't have leading or trailing spaces.",
        "err_email_too_long": "email is too long.",
        "err_email_missing_at": "give an address with @, e.g. name@example.org.",
        "err_email_multiple_at": "the email must have a single @.",
        "err_email_invalid_format": "invalid email format.",
        "err_private_key_pasted": (
            "this looks like a **private** key. Never paste that here. "
            "Paste only the **public** key line (.pub)."
        ),
        "err_pubkey_required": "the public key is required.",
        "err_pubkey_line_too_long": "key line is too long.",
        "err_pubkey_single_line": "paste a single line, with no line breaks.",
        "err_pubkey_empty": "public key is empty.",
        "err_pubkey_malformed": "malformed format: expected type, base64 data, and optional comment.",
        "err_pubkey_unsupported_type": (
            "key type not accepted ({key_type!r}). "
            "Examples: ssh-ed25519, ecdsa-sha2-nistp256, ssh-rsa."
        ),
        "err_pubkey_invalid_base64": "invalid key (base64) data.",
        "err_pubkey_rejected_by_sshkeygen": "the key was rejected by ssh-keygen: {err}",
        "err_sshkeygen_no_output": "ssh-keygen returned no output",
        "err_sshkeygen_no_fingerprint": "could not read the fingerprint: {out!r}",
    },
}


def t(lang: str, key: str, **kwargs: object) -> str:
    """Busca ``key`` no idioma pedido (cai para :data:`DEFAULT_LANG` se faltar)."""
    table = STRINGS.get(lang) or STRINGS[DEFAULT_LANG]
    text = table.get(key)
    if text is None:
        text = STRINGS[DEFAULT_LANG][key]
    if kwargs:
        return text.format(**kwargs)
    return text
