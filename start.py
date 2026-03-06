import subprocess
import sys
import os
import signal

def main():
    """Запускает Telegram и Slack ботов параллельно."""
    processes = []

    # Запускаем Telegram-бота
    print("🚀 Запуск Telegram-бота...")
    tg = subprocess.Popen([sys.executable, "bot.py"])
    processes.append(tg)

    # Запускаем Slack-бота
    print("🚀 Запуск Slack-бота...")
    slack = subprocess.Popen([sys.executable, "slack_bot.py"])
    processes.append(slack)

    def shutdown(signum, frame):
        print("⏹ Останавливаем ботов...")
        for p in processes:
            p.terminate()
        sys.exit(0)

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    # Ждём завершения любого из процессов
    for p in processes:
        p.wait()


if __name__ == "__main__":
    main()
