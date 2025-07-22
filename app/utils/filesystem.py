def create_user_folders(user_id: uuid.UUID) -> dict[str, bool]:
    """
    Create avatar and models folders for the given user ID.
    Returns a dict with path strings and bool success flags.
    """
    user_dir = UPLOADS_ROOT / str(user_id)
    avatars_dir = user_dir / "avatars"
    models_dir = user_dir / "models"

    result: dict[str, bool] = {}

    for path in [avatars_dir, models_dir]:
        try:
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ Created folder: {path}")
            result[str(path)] = True
        except Exception as e:
            logger.error(f"❌ Failed to create folder {path}: {e}")
            result[str(path)] = False

    return result
