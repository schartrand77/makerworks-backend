def model_to_dict(model: ModelMetadata):
    return {
        "id": model.id,
        "name": model.name,
        "uploader": model.uploader,
        "uploaded_at": model.uploaded_at.isoformat(),
        "preview_image": model.preview_image,
    }