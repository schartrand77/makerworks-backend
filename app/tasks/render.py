from app.worker import celery_app

@celery_app.task
def generate_gcode(model_id: int, estimate_id: int):
    print(f"[TASK] Generating G-code for model {model_id}, estimate {estimate_id}")
    # TODO: Actual G-code rendering logic
    return True