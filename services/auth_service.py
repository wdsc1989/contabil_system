"""
Serviço de autenticação e controle de acesso
"""
import bcrypt
import streamlit as st
from sqlalchemy.orm import Session
from models.user import User, UserClientPermission
from models.client import Client
from typing import Optional, List, Dict


class AuthService:
    """
    Serviço para gerenciar autenticação e permissões
    """

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Gera hash da senha usando bcrypt
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """
        Verifica se a senha corresponde ao hash
        """
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

    @staticmethod
    def authenticate(db: Session, username: str, password: str) -> Optional[User]:
        """
        Autentica um usuário
        """
        user = db.query(User).filter(
            User.username == username,
            User.active == True
        ).first()

        if user and AuthService.verify_password(password, user.password_hash):
            return user
        return None

    @staticmethod
    def create_user(db: Session, username: str, password: str, email: str, role: str) -> User:
        """
        Cria um novo usuário
        """
        password_hash = AuthService.hash_password(password)
        user = User(
            username=username,
            password_hash=password_hash,
            email=email,
            role=role,
            active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def get_user_clients(db: Session, user_id: int) -> List[Client]:
        """
        Retorna lista de clientes que o usuário tem acesso
        """
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            return []
        
        # Admin tem acesso a todos os clientes
        if user.role == 'admin':
            return db.query(Client).filter(Client.active == True).all()
        
        # Outros usuários só veem clientes com permissão
        permissions = db.query(UserClientPermission).filter(
            UserClientPermission.user_id == user_id,
            UserClientPermission.can_view == True
        ).all()
        
        client_ids = [p.client_id for p in permissions]
        return db.query(Client).filter(
            Client.id.in_(client_ids),
            Client.active == True
        ).all()

    @staticmethod
    def check_permission(db: Session, user_id: int, client_id: int, permission_type: str) -> bool:
        """
        Verifica se o usuário tem permissão específica para um cliente
        permission_type: 'view', 'edit', 'delete'
        """
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user or not user.active:
            return False
        
        # Admin tem todas as permissões
        if user.role == 'admin':
            return True
        
        # Verifica permissão específica
        perm = db.query(UserClientPermission).filter(
            UserClientPermission.user_id == user_id,
            UserClientPermission.client_id == client_id
        ).first()
        
        if not perm:
            return False
        
        if permission_type == 'view':
            return perm.can_view
        elif permission_type == 'edit':
            return perm.can_edit
        elif permission_type == 'delete':
            return perm.can_delete
        
        return False

    @staticmethod
    def grant_permission(db: Session, user_id: int, client_id: int, 
                        can_view: bool = True, can_edit: bool = False, 
                        can_delete: bool = False) -> UserClientPermission:
        """
        Concede permissão a um usuário para um cliente
        """
        # Verifica se já existe permissão
        perm = db.query(UserClientPermission).filter(
            UserClientPermission.user_id == user_id,
            UserClientPermission.client_id == client_id
        ).first()
        
        if perm:
            # Atualiza permissão existente
            perm.can_view = can_view
            perm.can_edit = can_edit
            perm.can_delete = can_delete
        else:
            # Cria nova permissão
            perm = UserClientPermission(
                user_id=user_id,
                client_id=client_id,
                can_view=can_view,
                can_edit=can_edit,
                can_delete=can_delete
            )
            db.add(perm)
        
        db.commit()
        db.refresh(perm)
        return perm

    @staticmethod
    def init_session_state():
        """
        Inicializa o estado da sessão do Streamlit
        """
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'user' not in st.session_state:
            st.session_state.user = None
        if 'selected_client_id' not in st.session_state:
            st.session_state.selected_client_id = None

    @staticmethod
    def login(user: User):
        """
        Realiza login do usuário na sessão
        """
        st.session_state.authenticated = True
        st.session_state.user = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role
        }

    @staticmethod
    def logout():
        """
        Realiza logout do usuário
        """
        st.session_state.authenticated = False
        st.session_state.user = None
        st.session_state.selected_client_id = None

    @staticmethod
    def is_authenticated() -> bool:
        """
        Verifica se há usuário autenticado
        """
        return st.session_state.get('authenticated', False)

    @staticmethod
    def get_current_user() -> Optional[Dict]:
        """
        Retorna dados do usuário atual
        """
        return st.session_state.get('user', None)

    @staticmethod
    def require_auth():
        """
        Decorator/função para exigir autenticação
        """
        if not AuthService.is_authenticated():
            st.warning("⚠️ Você precisa fazer login para acessar esta página.")
            st.stop()

    @staticmethod
    def require_role(allowed_roles: List[str]):
        """
        Verifica se o usuário tem uma das roles permitidas
        """
        AuthService.require_auth()
        user = AuthService.get_current_user()
        if user['role'] not in allowed_roles:
            st.error("❌ Você não tem permissão para acessar esta página.")
            st.stop()




