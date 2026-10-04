"""Run the synthetic baseline without a web server: python -m app."""

from app.domain.assumptions import Assumptions
from app.domain.evaluation import evaluate

if __name__ == "__main__":
    print(evaluate(Assumptions()).model_dump_json(indent=2))
