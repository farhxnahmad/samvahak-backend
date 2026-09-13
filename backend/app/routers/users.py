from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.deps import require_roles
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.user import UserAdminOut, UserRoleUpdate, UserActiveUpdate

router = APIRouter(prefix="/api/users", tags=["users"])

# Every endpoint here is Admin-only — this is the Admin Panel's "manage users" surface.
_admin_only = require_roles(UserRole.ADMIN)


@router.get("", response_model=list[UserAdminOut])
def list_users(role: str | None = None, db: Session = Depends(get_db), _=Depends(_admin_only)):
    q = db.query(User)
    if role:
        q = q.filter(User.role == role)
    return q.order_by(User.full_name).all()


@router.get("/{user_id}", response_model=UserAdminOut)
def get_user(user_id: int, db: Session = Depends(get_db), _=Depends(_admin_only)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{user_id}/role", response_model=UserAdminOut)
def change_user_role(user_id: int, payload: UserRoleUpdate, db: Session = Depends(get_db), _=Depends(_admin_only)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = payload.role
    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}/active", response_model=UserAdminOut)
def set_user_active(user_id: int, payload: UserActiveUpdate, db: Session = Depends(get_db), _=Depends(_admin_only)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = payload.is_active
    db.commit()
    db.refresh(user)
    return user
