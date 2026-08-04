# Sandbox

Default `SandboxPolicy`:

- No network  
- No subprocess from native code (pytest runner is controlled)  
- Import allowlist: stdlib subset + `linguini.*`  
- Banned: `socket`, `subprocess`, `requests`, `os.system`, …  

Natives are statically scanned before load/exec. Untested code is never written to the registry.
