diff --git a/chrome/browser/browseros_server/browseros_server_prefs.h b/chrome/browser/browseros_server/browseros_server_prefs.h
new file mode 100644
index 0000000000000..974b18422a083
--- /dev/null
+++ b/chrome/browser/browseros_server/browseros_server_prefs.h
@@ -0,0 +1,28 @@
+// Copyright 2024 The Chromium Authors
+// Use of this source code is governed by a BSD-style license that can be
+// found in the LICENSE file.
+
+#ifndef CHROME_BROWSER_BROWSEROS_SERVER_BROWSEROS_SERVER_PREFS_H_
+#define CHROME_BROWSER_BROWSEROS_SERVER_BROWSEROS_SERVER_PREFS_H_
+
+class PrefRegistrySimple;
+
+namespace browseros_server {
+
+// Default port values for BrowserOS server (10-port spacing)
+inline constexpr int kDefaultCDPPort = 9223;
+inline constexpr int kDefaultMCPPort = 9233;
+inline constexpr int kDefaultAgentPort = 9243;
+
+// Preference keys for BrowserOS server configuration
+extern const char kCDPServerPort[];
+extern const char kMCPServerPort[];
+extern const char kAgentServerPort[];
+extern const char kMCPServerEnabled[];
+
+// Registers BrowserOS server preferences in Local State (browser-wide prefs)
+void RegisterLocalStatePrefs(PrefRegistrySimple* registry);
+
+}  // namespace browseros_server
+
+#endif  // CHROME_BROWSER_BROWSEROS_SERVER_BROWSEROS_SERVER_PREFS_H_
