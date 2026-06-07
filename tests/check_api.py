import inspect
from transformers import AutoProcessor
p = AutoProcessor.from_pretrained("IDEA-Research/grounding-dino-tiny")
sig = inspect.signature(p.post_process_grounded_object_detection)
print("Signature:", sig)
print("Params:", list(sig.parameters.keys()))
