async def upsert_user_from_token(db: AsyncSession, token_payload: dict) -> User:
    sub = token_payload["sub"]
    email = token_payload["email"]
    username = token_payload.get("preferred_username") or email.split("@")[0]

    result = await db.execute(select(User).where(User.id == sub))
    user = result.scalar_one_or_none()

    if user:
        user.last_login = datetime.utcnow()
    else:
        user = User(
            id=sub,
            email=email,
            username=username,
            is_verified=True,
            is_active=True,
            role=token_payload.get("role", "user"),
        )
        db.add(user)

    await db.commit()
    await db.refresh(user)
    return user
