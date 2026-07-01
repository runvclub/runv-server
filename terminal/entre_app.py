#!/usr/bin/env python3
"""
Experiência SSH guiada para pedidos de entrada na runv.club (utilizador «entre»).

Executado via ForceCommand no OpenSSH. Não cria contas Linux; apenas fila + log
+ notificação opcional.

Bilíngue: a primeira tela pergunta Português/English (choose_language()) e essa
escolha vale para toda a sessão — prompts, mensagens de validação, ecrã final.
Textos em terminal/i18n.py; templates localizados em terminal/templates/<lang>/
com fallback para o pt-BR em terminal/templates/ quando o arquivo localizado
não existir (ver template_for()). Os templates admin_console_notice.txt e
admin_mail.txt (lidos só pelo admin) permanecem em português sempre.

Versão 0.03 — runv.club
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Arte ASCII da landing (site/public/index.html) — manter alinhado ao <pre class="ascii">.
RUNV_ASCII_ART: str = """██████╗ ██╗   ██╗███╗   ██╗██╗   ██╗
██╔══██╗██║   ██║████╗  ██║██║   ██║
██████╔╝██║   ██║██╔██╗ ██║██║   ██║
██╔══██╗╚██╗ ██╔╝██║╚██╗██║╚██╗ ██╔╝
██║  ██║ ╚████╔╝ ██║ ╚████║ ╚████╔╝
╚═╝  ╚═╝  ╚═══╝  ╚═╝  ╚═══╝  ╚═══╝"""

# Em intro.txt: linha só com este marcador separa ecrãs da narrativa.
INTRO_PAGE_BREAK: str = "%%PAGE%%"

from entre_core import (
    APP_VERSION,
    MAX_ONLINE_PRESENCE_LEN,
    ValidationError,
    build_request_payload,
    find_config_path,
    find_install_root,
    load_config,
    log_session,
    new_request_id,
    render_template,
    resolve_entre_notify_recipients,
    resolve_paths,
    save_request_json,
    sendmail_notify,
    setup_file_logger,
    ssh_remote_context,
    validate_email,
    validate_online_presence,
    validate_public_key_line,
    validate_username,
)
from i18n import DEFAULT_LANG, t


def eprint(msg: str) -> None:
    print(msg, file=sys.stderr)


def pause(stdin, stdout, lang: str) -> None:
    stdout.write(t(lang, "pause_prompt"))
    stdout.flush()
    line = stdin.readline()
    if not line:
        raise SystemExit(0)
    if line.strip().lower() in ("q", "quit", "sair", "exit"):
        print(t(lang, "goodbye_quit"))
        raise SystemExit(0)


def read_line(prompt: str, stdin, stdout) -> str:
    stdout.write(prompt)
    stdout.flush()
    line = stdin.readline()
    if not line:
        raise SystemExit(0)
    return line.rstrip("\r\n")


def write_data_step_header(stdout, step: int, total: int, title: str, lang: str) -> None:
    """Cabeçalho visível antes de cada campo do formulário."""
    clear_screen(stdout)
    g = "\033[92m" if _use_ansi_color(stdout) else ""
    c = "\033[96m" if _use_ansi_color(stdout) else ""
    b = "\033[1m" if _use_ansi_color(stdout) else ""
    r = "\033[0m" if g else ""
    bar = "━" * 52
    stdout.write(f"\n  {g}{bar}{r}\n")
    stdout.write(f"  {b}{c}{t(lang, 'step_header_label', step=step, total=total)}{r}\n")
    stdout.write(f"  {b}{g}{title}{r}\n")
    stdout.write(f"  {g}{bar}{r}\n\n")


def read_multiline_until_dot(stdin, stdout, lang: str, *, max_lines: int = 48) -> str:
    """Várias linhas; termina com uma linha só com '.' (como no SMTP clássico)."""
    d = "\033[2m" if _use_ansi_color(stdout) else ""
    r = "\033[0m" if d else ""
    stdout.write(f"{d}  {t(lang, 'multiline_hint')}{r}\n\n")
    stdout.flush()
    lines: list[str] = []
    for _ in range(max_lines):
        line = stdin.readline()
        if not line:
            raise SystemExit(0)
        s = line.rstrip("\r\n")
        if s == ".":
            if lines:
                break
            continue
        lines.append(s)
        if len("\n".join(lines)) > MAX_ONLINE_PRESENCE_LEN:
            stdout.write(f"\n  {d}{t(lang, 'multiline_size_limit')}{r}\n")
            break
    return "\n".join(lines).strip()


def clear_screen(stdout) -> None:
    stdout.write("\033[2J\033[H")
    stdout.flush()


def _use_ansi_color(stdout) -> bool:
    if not getattr(stdout, "isatty", lambda: False)():
        return False
    term = (os.environ.get("TERM") or "").strip().lower()
    if term in ("", "dumb"):
        return False
    if os.environ.get("NO_COLOR", "").strip():
        return False
    return True


RUNV_CLUB_MARK: str = "runv.club"


def style_runv_club(text: str, stdout) -> str:
    """Destaca runv.club a verde no terminal (todas as ocorrências)."""
    if not _use_ansi_color(stdout) or RUNV_CLUB_MARK not in text:
        return text
    g, r = "\033[92m", "\033[0m"
    return text.replace(RUNV_CLUB_MARK, f"{g}{RUNV_CLUB_MARK}{r}")


def wait_any_key(stdin, stdout, lang: str) -> None:
    """Lê uma tecla em modo cru (POSIX); senão, uma linha (Enter)."""
    if sys.platform != "win32" and stdin.isatty():
        try:
            import termios
            import tty

            fd = stdin.fileno()
            old = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                ch = stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old)
            if ch == "\x03":
                raise KeyboardInterrupt
            if ch == "\x04" or ch == "":
                raise SystemExit(0)
            return
        except (ImportError, OSError, termios.error):
            pass
    stdout.write(t(lang, "press_enter_hint"))
    stdout.flush()
    line = stdin.readline()
    if not line:
        raise SystemExit(0)


def choose_language(stdin, stdout) -> str:
    """
    Primeira tela da sessão — bilíngue por construção (não usa i18n.t, é a
    própria escolha de idioma). A resposta vale para toda a sessão.
    """
    clear_screen(stdout)
    stdout.write("\n  runv.club\n\n")
    stdout.write("  Português ou English?\n\n")
    stdout.write("  [1] Português (padrão / default)\n")
    stdout.write("  [2] English\n\n")
    stdout.write("Opção / Option: ")
    stdout.flush()
    line = stdin.readline()
    if not line:
        raise SystemExit(0)
    choice = line.strip().lower()
    if choice in ("2", "en", "english"):
        return "en"
    return DEFAULT_LANG


def template_for(templates: Path, name: str, lang: str) -> Path:
    """Versão localizada (templates/<lang>/<name>) se existir; senão o pt-BR de sempre."""
    if lang != DEFAULT_LANG:
        candidate = templates / lang / name
        if candidate.is_file():
            return candidate
    return templates / name


def show_opening_splash(stdin, stdout, lang: str) -> None:
    clear_screen(stdout)
    green = "\033[92m" if _use_ansi_color(stdout) else ""
    reset = "\033[0m" if green else ""
    stdout.write("\n")
    for line in RUNV_ASCII_ART.splitlines():
        stdout.write(f"  {green}{line}{reset}\n")
    stdout.write(f"\n  {green}{t(lang, 'ascii_tagline')}{reset}\n\n")
    stdout.write(f"  {green}{t(lang, 'press_any_key')}{reset}\n")
    stdout.flush()
    wait_any_key(stdin, stdout, lang)


def show_paged_template(stdin, stdout, template_path: Path, lang: str) -> None:
    raw = template_path.read_text(encoding="utf-8")
    pages = [p.strip("\n") for p in raw.split(INTRO_PAGE_BREAK)]
    pages = [p for p in pages if p.strip()]
    total = len(pages)
    for i, page in enumerate(pages, start=1):
        clear_screen(stdout)
        if total > 1:
            stdout.write(f"  ({i}/{total})\n\n")
        page = style_runv_club(page, stdout)
        stdout.write(page)
        if not page.endswith("\n"):
            stdout.write("\n")
        stdout.flush()
        pause(stdin, stdout, lang)


def collect_loop(stdin, stdout, templates: Path, lang: str) -> tuple[str, str, str, str, str]:
    username = email = online_presence = pubkey = ""
    fp = ""
    total = 4
    while True:
        write_data_step_header(stdout, 1, total, t(lang, "step1_title"), lang)
        stdout.write(style_runv_club(t(lang, "step1_help"), stdout))
        b = "\033[1m" if _use_ansi_color(stdout) else ""
        r = "\033[0m" if b else ""
        stdout.write(f"\n  {b}{t(lang, 'input_marker_write')}{r}\n\n  ")
        stdout.flush()
        u = read_line("", stdin, stdout).strip()
        if u:
            username = u

        write_data_step_header(stdout, 2, total, t(lang, "step2_title"), lang)
        stdout.write(t(lang, "step2_help"))
        stdout.write(f"\n  {b}{t(lang, 'input_marker_write')}{r}\n\n  ")
        stdout.flush()
        e = read_line("", stdin, stdout).strip()
        if e:
            email = e

        write_data_step_header(stdout, 3, total, t(lang, "step3_title"), lang)
        stdout.write(style_runv_club(t(lang, "step3_help"), stdout))
        stdout.write(f"\n  {b}{t(lang, 'input_marker_multiline')}{r}\n")
        stdout.flush()
        raw_on = read_multiline_until_dot(stdin, stdout, lang)
        if raw_on:
            online_presence = raw_on

        write_data_step_header(stdout, 4, total, t(lang, "step4_title"), lang)
        stdout.write(t(lang, "step4_help"))
        stdout.write(f"\n  {b}{t(lang, 'input_marker_paste')}{r}\n\n  ")
        stdout.flush()
        pk = stdin.readline()
        if not pk:
            raise SystemExit(0)
        pk = pk.rstrip("\r\n")
        if pk.strip():
            pubkey = pk.strip()

        errors: list[str] = []
        try:
            vu = validate_username(username, lang)
        except ValidationError as ex:
            errors.append(str(ex))
            vu = ""
        try:
            ve = validate_email(email, lang)
        except ValidationError as ex:
            errors.append(str(ex))
            ve = ""
        try:
            v_on = validate_online_presence(online_presence, lang)
        except ValidationError as ex:
            errors.append(str(ex))
            v_on = ""
        try:
            if not pubkey:
                raise ValidationError(t(lang, "err_pubkey_required"))
            nkey, fp = validate_public_key_line(pubkey, lang)
        except ValidationError as ex:
            errors.append(str(ex))
            nkey, fp = "", ""

        if errors:
            clear_screen(stdout)
            stdout.write(f"{t(lang, 'fix_errors_header')}\n\n")
            for err in errors:
                stdout.write(f"  • {err}\n")
            stdout.write(t(lang, "back_to_form_hint"))
            stdout.flush()
            stdin.readline()
            continue
        return vu, ve, v_on, nkey, fp


def confirm_loop(
    stdin,
    stdout,
    *,
    username: str,
    email: str,
    online_presence: str,
    fingerprint: str,
    templates: Path,
    lang: str,
) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    body = render_template(
        template_for(templates, "confirm.txt", lang),
        {
            "username": username,
            "email": email,
            "online_presence": online_presence,
            "fingerprint": fingerprint,
            "submitted_preview": now,
        },
    )
    while True:
        clear_screen(stdout)
        stdout.write(style_runv_club(body, stdout))
        stdout.write(f"\n{t(lang, 'confirm_option_confirm')}\n")
        stdout.write(f"{t(lang, 'confirm_option_edit')}\n")
        stdout.write(f"{t(lang, 'confirm_option_cancel')}\n\n")
        stdout.write(t(lang, "confirm_prompt_label"))
        stdout.flush()
        line = stdin.readline()
        if not line:
            raise SystemExit(0)
        c = line.strip().lower()
        if c in ("c", "confirmar", "confirm", "s", "sim", "y", "yes"):
            return "confirm"
        if c in ("e", "editar", "edit"):
            return "edit"
        if c in ("x", "cancelar", "cancel", "n", "nao", "não", "no"):
            return "cancel"
        stdout.write(f"{t(lang, 'confirm_invalid_option')}\n")
        stdout.write("[Enter]")
        stdin.readline()


def main() -> int:
    parser = argparse.ArgumentParser(description="Fluxo SSH entre@runv.club (runv.club)")
    parser.add_argument("--version", action="version", version=f"%(prog)s {APP_VERSION}")
    args = parser.parse_args()
    del args

    stdin, stdout = sys.stdin, sys.stdout

    install_root = find_install_root()
    config_path = find_config_path(install_root)
    try:
        cfg = load_config(config_path)
    except (OSError, ValueError) as e:
        eprint(f"Erro de configuração: {e}")
        return 2

    paths = resolve_paths(cfg, install_root)
    logger = setup_file_logger(paths.log_file)

    ctx = ssh_remote_context()
    log_session(
        logger,
        f"sessão iniciada remote_addr={ctx.get('remote_addr')!r} tty={ctx.get('tty')!r}",
    )

    templates = paths.templates_dir
    if not templates.is_dir():
        eprint(f"Templates em falta: {templates}")
        log_session(logger, f"ERRO templates em falta: {templates}", level=40)
        return 2

    try:
        # --- Idioma: primeira pergunta da sessão, vale para toda a interação
        lang = choose_language(stdin, stdout)
        log_session(logger, f"idioma escolhido: {lang!r}")

        # --- Abertura: arte ASCII da landing (verde) + qualquer tecla
        show_opening_splash(stdin, stdout, lang)

        # --- Etapa 1: narrativa (%%PAGE%% em intro.txt)
        show_paged_template(stdin, stdout, template_for(templates, "intro.txt", lang), lang)

        # --- Etapa 2: aviso chave (pode ter %%PAGE%% como intro.txt)
        show_paged_template(
            stdin, stdout, template_for(templates, "warning_public_key.txt", lang), lang
        )

        # --- Etapa 3–4: coleta e confirmação (com edição repetível)
        username, email, online_presence, pubkey, fingerprint = collect_loop(
            stdin, stdout, templates, lang
        )
        while True:
            action = confirm_loop(
                stdin,
                stdout,
                username=username,
                email=email,
                online_presence=online_presence,
                fingerprint=fingerprint,
                templates=templates,
                lang=lang,
            )
            if action == "cancel":
                log_session(logger, "utilizador cancelou antes de gravar")
                stdout.write(t(lang, "request_cancelled"))
                return 0
            if action == "edit":
                username, email, online_presence, pubkey, fingerprint = collect_loop(
                    stdin, stdout, templates, lang
                )
                continue
            break

        request_id = ""
        path_saved = None
        for attempt in range(8):
            request_id = new_request_id()
            payload = build_request_payload(
                request_id=request_id,
                username=username,
                email=email,
                online_presence=online_presence,
                public_key=pubkey,
                fingerprint=fingerprint,
                remote_addr=ctx.get("remote_addr"),
                tty=ctx.get("tty"),
                lang=lang,
            )
            try:
                path_saved = save_request_json(
                    queue_dir=paths.queue_dir,
                    request_id=request_id,
                    payload=payload,
                    logger=logger,
                )
                break
            except FileExistsError:
                log_session(logger, f"colisão request_id, a gerar outro (tentativa {attempt + 1})")
                continue
            except OSError as e:
                log_session(logger, f"ERRO ao gravar pedido: {e}", level=40)
                eprint("Não foi possível gravar o pedido. Contacte a administração.")
                return 2
        else:
            log_session(logger, "ERRO: não foi possível obter request_id único", level=40)
            eprint("Erro interno: tente novamente.")
            return 2

        submitted_at = payload["submitted_at"]
        _ = path_saved

        # Aviso em consola ao admin (template curto) — sempre em pt; inclui o
        # idioma escolhido pelo visitante como referência para o admin.
        try:
            oneline = online_presence.replace("\n", " ").strip()
            if len(oneline) > 100:
                oneline = oneline[:97] + "..."
            notice = render_template(
                templates / "admin_console_notice.txt",
                {
                    "request_id": request_id,
                    "username": username,
                    "email": email,
                    "fingerprint": fingerprint,
                    "submitted_at": submitted_at,
                    "online_presence_line": oneline,
                    "lang": lang,
                },
            )
            log_session(logger, "admin_console_notice:\n" + notice.strip())
        except OSError:
            pass

        admin_email, mail_from = resolve_entre_notify_recipients(cfg, logger=logger)
        sendmail_path = str(cfg.get("sendmail_path", "/usr/sbin/sendmail")).strip()
        if admin_email:
            try:
                subject = f"[runv] Novo pedido: {username}"
                body = render_template(
                    templates / "admin_mail.txt",
                    {
                        "request_id": request_id,
                        "username": username,
                        "email": email,
                        "online_presence": online_presence,
                        "public_key": pubkey,
                        "fingerprint": fingerprint,
                        "submitted_at": submitted_at,
                        "remote_addr": ctx.get("remote_addr") or "",
                        "tty": ctx.get("tty") or "",
                        "lang": lang,
                    },
                )
                sendmail_notify(
                    admin_email=admin_email,
                    mail_from=mail_from,
                    subject=subject,
                    body=body,
                    sendmail_path=sendmail_path,
                    logger=logger,
                )
            except OSError as e:
                log_session(logger, f"template admin_mail falhou: {e}", level=40)

        # --- Etapa 7: despedida
        clear_screen(stdout)
        goodbye = render_template(
            template_for(templates, "goodbye.txt", lang),
            {"request_id": request_id},
        )
        stdout.write(style_runv_club(goodbye, stdout))
        stdout.flush()
        log_session(logger, f"sessão concluída request_id={request_id}")
    except ValidationError as e:
        log_session(logger, f"validação: {e}", level=40)
        stdout.write(style_runv_club(f"\n{e}\n\n", stdout))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
