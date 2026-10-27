"use client";

import { useEffect } from "react";

type TgWebApp = { ready(): void; expand(): void };

declare global {
  interface Window {
    Telegram?: { WebApp?: TgWebApp };
  }
}

// В Telegram сообщает клиенту, что страница готова, и раскрывает окно.
// В обычном браузере window.Telegram.WebApp пуст, поэтому ничего не ломается.
export default function TelegramInit() {
  useEffect(() => {
    const tg = window.Telegram?.WebApp;
    tg?.ready();
    tg?.expand();
  }, []);

  return null;
}
