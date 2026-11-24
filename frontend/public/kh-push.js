// KH: push messages of "Mitteilungen" (D75), loaded into the app's service worker (importScripts in kh/nuxt.config.ts).
// A message shows as a notification; a tap opens its page in the app, in a window that is already open if there is one.
self.addEventListener("push", (event) => {
  let message = {};
  try {
    message = event.data ? event.data.json() : {};
  }
  catch {
    message = { body: event.data ? event.data.text() : "" };
  }
  event.waitUntil(
    self.registration.showNotification(message.title || (/^de/i.test(self.navigator.language) ? "Kochheft" : "Cookbook"), {
      body: message.body || "",
      icon: "/icons/android-chrome-192x192.png",
      data: { url: message.url || "/" },
    }),
  );
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  // Only pages of this app: anything else opens the start page
  const target = new URL((event.notification.data && event.notification.data.url) || "/", self.location.origin);
  const url = target.origin === self.location.origin ? target.href : self.location.origin + "/";
  event.waitUntil(
    self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((windows) => {
      const open = windows.find(client => client.url.startsWith(self.location.origin) && "focus" in client);
      if (!open) return self.clients.openWindow(url);
      return open.focus().then(client => (client && "navigate" in client ? client.navigate(url) : undefined));
    }),
  );
});
