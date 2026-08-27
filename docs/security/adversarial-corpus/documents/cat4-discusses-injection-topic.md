# Understanding Prompt Injection Attacks

Prompt injection is a class of attack where malicious text such as "ignore previous instructions" is embedded in retrieved content, attempting to make a language model follow the embedded text instead of its actual instructions.

Security researchers study this class of attack so that systems retrieving untrusted documents can be designed to resist it, typically through structural defenses such as delimiting untrusted content rather than relying on the model to recognize the attempt unaided.
