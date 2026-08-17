PYTHON ?= python3
PYTHONPATH := src

.PHONY: all reproduce verify benchmark guide test clean release

all: verify

reproduce:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m causalcred_eval reproduce --root .

verify: reproduce test
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m causalcred_eval verify --root .

benchmark:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m causalcred_eval benchmark --root .

guide:
	$(PYTHON) scripts/build_artifact_guide.py --root . --output docs/CausalCred_Artifact_Guide.pdf

test:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m unittest discover -s tests -v

release: verify
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) scripts/build_release.py --root . --output ../CausalCred-artifact.zip

clean:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m causalcred_eval clean --root .
