"""The team's future model connection goes here. No fake predictions are produced."""
def predict(dataset):
    """Return a DataFrame with patient_id,date,risk_score,risk_level and optional reasons.

    Load the team's model and preprocessing here, or call the team's actual API.
    Dataset upload alone is NOT model inference. Nothing calls this function yet.
    """
    raise NotImplementedError('Connect the team model before enabling inference.')
