from fastapi import APIRouter, Depends, HTTPException, status
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Optional, List
from auth.jwt_handler import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_token,
)
from auth.models import User, UserRole
from auth.schemas import UserCreate, UserLogin, Token, UserResponse, UserUpdate, TokenRefresh, PasswordChange
from auth.dependencies import get_current_user, require_admin
from database import get_db

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Check if username already exists
    existing_username = db.query(User).filter(User.username == user_data.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )

    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password,
        role=user_data.role,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Login and get access + refresh tokens"""
    user = db.query(User).filter(User.email == credentials.email).first()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    # Create tokens
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "username": user.username}
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.id), "email": user.email, "username": user.username}
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(token_data: TokenRefresh, db: Session = Depends(get_db)):
    """Refresh access token using refresh token"""
    payload = verify_token(token_data.refresh_token)

    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == int(user_id)).first()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Create new access token
    new_access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "username": user.username}
    )
    new_refresh_token = create_refresh_token(
        data={"sub": str(user.id), "email": user.email, "username": user.username}
    )

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user information"""
    return current_user


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change current user password"""
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password",
        )
    
    current_user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()
    return {"status": "success", "message": "Password changed successfully"}


@router.get("/users", response_model=List[UserResponse], dependencies=[Depends(require_admin)])
async def list_users(role: Optional[UserRole] = None, db: Session = Depends(get_db)):
    try:
        query = db.query(User)
        if role:
            query = query.filter(User.role == role)
        users = query.all()
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
async def create_user_admin(user_data: UserCreate, db: Session = Depends(get_db)):
    """Create a new user (admin only)"""
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Check if username already exists
    existing_username = db.query(User).filter(User.username == user_data.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )

    # Send credentials via email before hashing
    try:
        sender_email = os.getenv("mail_@")
        sender_password = os.getenv("mail_code")
        
        if sender_email and sender_password:
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = user_data.email
            msg['Subject'] = "Your New Account Credentials"
            
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    .container {{
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        max-width: 600px;
                        margin: 0 auto;
                        background-color: #ffffff;
                        border-radius: 16px;
                        overflow: hidden;
                        box-shadow: 0 4px 20px rgba(0,0,0,0.05);
                        border: 1px solid #e2e8f0;
                    }}
                    .header {{
                        background: linear-gradient(135deg, #f97316, #8b5cf6);
                        padding: 40px 20px;
                        text-align: center;
                        color: white;
                    }}
                    .content {{
                        padding: 40px 30px;
                        color: #1e293b;
                        line-height: 1.6;
                    }}
                    .credentials-card {{
                        background-color: #f8fafc;
                        border-radius: 12px;
                        padding: 24px;
                        margin: 24px 0;
                        border: 1px solid #e2e8f0;
                    }}
                    .credential-item {{
                        padding: 12px 0;
                        border-bottom: 1px solid #f1f5f9;
                    }}
                    .credential-item:last-child {{
                        border-bottom: none;
                    }}
                    .label {{
                        color: #64748b;
                        font-weight: 600;
                        font-size: 0.75rem;
                        text-transform: uppercase;
                        letter-spacing: 0.05em;
                        display: block;
                        margin-bottom: 4px;
                    }}
                    .value {{
                        color: #0f172a;
                        font-weight: 700;
                        font-size: 1.1rem;
                        display: block;
                    }}
                    .footer {{
                        padding: 30px;
                        text-align: center;
                        color: #94a3b8;
                        font-size: 0.8rem;
                        background-color: #f8fafc;
                        border-top: 1px solid #f1f5f9;
                    }}
                    .btn {{
                        display: inline-block;
                        padding: 16px 32px;
                        background: linear-gradient(135deg, #f97316, #ea580c);
                        color: #ffffff !important;
                        text-decoration: none;
                        border-radius: 12px;
                        font-weight: 700;
                        margin-top: 20px;
                        box-shadow: 0 4px 12px rgba(249, 115, 22, 0.3);
                    }}
                </style>
            </head>
            <body style="background-color: #f8fafc; padding: 40px 20px; margin: 0;">
                <div class="container">
                    <div class="header">
                        <h1 style="margin: 0; font-size: 28px; font-weight: 800; letter-spacing: -0.02em;">Orange Analytics</h1>
                    </div>
                    <div class="content">
                        <h2 style="margin-top: 0; color: #0f172a; font-size: 20px;">Welcome, {user_data.username}!</h2>
                        <p style="font-size: 16px; color: #475569;">Your administrative account has been created. Use the following credentials to access the secure dashboard:</p>
                        
                        <div class="credentials-card">
                            <div class="credential-item">
                                <span class="label">Email Address</span>
                                <span class="value">{user_data.email}</span>
                            </div>
                            <div class="credential-item">
                                <span class="label">Username</span>
                                <span class="value">{user_data.username}</span>
                            </div>
                            <div class="credential-item">
                                <span class="label">Temporary Password</span>
                                <span class="value" style="color: #f97316;">{user_data.password}</span>
                            </div>
                            <div class="credential-item">
                                <span class="label">Assigned Role</span>
                                <span class="value">{user_data.role}</span>
                            </div>
                        </div>
                        
                        <div style="background-color: #fff7ed; border-left: 4px solid #f97316; padding: 16px; margin: 24px 0; border-radius: 8px;">
                            <p style="margin: 0; color: #9a3412; font-size: 14px; font-weight: 500;">
                                <strong>Security Notice:</strong> This is a temporary password. For security reasons, please update your password immediately after logging in.
                            </p>
                        </div>
                        
                        <div style="text-align: center; margin-top: 32px;">
                            <a href="#" class="btn">Access Dashboard</a>
                        </div>
                    </div>
                    <div class="footer">
                        <p style="margin: 0;">&copy; 2026 Orange Analytics &bull; Security & Analysis Suite</p>
                        <p style="margin: 4px 0 0 0;">This is an automated message, please do not reply.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html_body, 'html'))
            
            # Using SMTP to send the email (IMAP is for reading/managing)
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(sender_email, sender_password)
                server.send_message(msg)
                print(f"Credentials sent to {user_data.email}")
    except Exception as e:
        print(f"Error sending credentials email: {str(e)}")

    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password,
        role=user_data.role,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.get("/users/{user_id}", response_model=UserResponse, dependencies=[Depends(require_admin)])
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get a specific user by ID (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.put("/users/{user_id}", response_model=UserResponse, dependencies=[Depends(require_admin)])
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
):
    """Update a user (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    if (user.is_active is not user_update.is_active) and user_update.is_active == False:
        try:
            sender_email = os.getenv("mail_@")
            sender_password = os.getenv("mail_code")

            if sender_email and sender_password:
                msg = MIMEMultipart()
                msg['From'] = sender_email
                msg['To'] = str(user.email)
                msg['Subject'] = "Your Account Has Been Disabled"

                html_body = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <style>
                        .container {{
                            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                            max-width: 600px;
                            margin: 0 auto;
                            background-color: #ffffff;
                            border-radius: 16px;
                            overflow: hidden;
                            box-shadow: 0 4px 20px rgba(0,0,0,0.05);
                            border: 1px solid #e2e8f0;
                        }}
                        .header {{
                            background: linear-gradient(135deg, #f97316, #8b5cf6);
                            padding: 40px 20px;
                            text-align: center;
                            color: white;
                        }}
                        .content {{
                            padding: 40px 30px;
                            color: #1e293b;
                            line-height: 1.6;
                        }}
                        .credentials-card {{
                            background-color: #f8fafc;
                            border-radius: 12px;
                            padding: 24px;
                            margin: 24px 0;
                            border: 1px solid #e2e8f0;
                        }}
                        .credential-item {{
                            padding: 12px 0;
                            border-bottom: 1px solid #f1f5f9;
                        }}
                        .credential-item:last-child {{
                            border-bottom: none;
                        }}
                        .label {{
                            color: #64748b;
                            font-weight: 600;
                            font-size: 0.75rem;
                            text-transform: uppercase;
                            letter-spacing: 0.05em;
                            display: block;
                            margin-bottom: 4px;
                        }}
                        .value {{
                            color: #0f172a;
                            font-weight: 700;
                            font-size: 1.1rem;
                            display: block;
                        }}
                        .footer {{
                            padding: 30px;
                            text-align: center;
                            color: #94a3b8;
                            font-size: 0.8rem;
                            background-color: #f8fafc;
                            border-top: 1px solid #f1f5f9;
                        }}
                        .btn {{
                            display: inline-block;
                            padding: 16px 32px;
                            background: linear-gradient(135deg, #f97316, #ea580c);
                            color: #ffffff !important;
                            text-decoration: none;
                            border-radius: 12px;
                            font-weight: 700;
                            margin-top: 20px;
                            box-shadow: 0 4px 12px rgba(249, 115, 22, 0.3);
                        }}
                    </style>
                </head>
                <body style="background-color: #f8fafc; padding: 40px 20px; margin: 0;">
                    <div class="container">
                        <div class="header">
                            <h1 style="margin: 0; font-size: 28px; font-weight: 800; letter-spacing: -0.02em;">Orange Analytics</h1>
                        </div>
                        <div class="content">
                            <h2 style="margin-top: 0; color: #0f172a; font-size: 20px;">Welcome, {user.username}!</h2>
                            <p style="font-size: 16px; color: #475569;">Your administrative account has been disabled.</p>

                            <div style="background-color: #fff7ed; border-left: 4px solid #f97316; padding: 16px; margin: 24px 0; border-radius: 8px;">
                                <p style="margin: 0; color: #9a3412; font-size: 14px; font-weight: 500;">
                                    <strong>Security Notice:</strong> Your administrative account has been disabled. If you believe this is a mistake, please contact your system administrator.
                                </p>
                            </div>
                        </div>
                        <div class="footer">
                            <p style="margin: 0;">&copy; 2026 Orange Analytics &bull; Security & Analysis Suite</p>
                            <p style="margin: 4px 0 0 0;">This is an automated message, please do not reply.</p>
                        </div>
                    </div>
                </body>
                </html>
                """

                msg.attach(MIMEText(html_body, 'html'))

                # Using SMTP to send the email (IMAP is for reading/managing)
                with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                    server.login(sender_email, sender_password)
                    server.send_message(msg)
                    print(f"message sent to {user.email}")
        except Exception as e:
            print(f"Error sending message email: {str(e)}")
    else:
        try:
            sender_email = os.getenv("mail_@")
            sender_password = os.getenv("mail_code")

            if sender_email and sender_password:
                msg = MIMEMultipart()
                msg['From'] = sender_email
                msg['To'] = str(user.email)
                msg['Subject'] = "Your Account Has Been Disabled"

                html_body = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <style>
                        .container {{
                            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                            max-width: 600px;
                            margin: 0 auto;
                            background-color: #ffffff;
                            border-radius: 16px;
                            overflow: hidden;
                            box-shadow: 0 4px 20px rgba(0,0,0,0.05);
                            border: 1px solid #e2e8f0;
                        }}
                        .header {{
                            background: linear-gradient(135deg, #f97316, #8b5cf6);
                            padding: 40px 20px;
                            text-align: center;
                            color: white;
                        }}
                        .content {{
                            padding: 40px 30px;
                            color: #1e293b;
                            line-height: 1.6;
                        }}
                        .credentials-card {{
                            background-color: #f8fafc;
                            border-radius: 12px;
                            padding: 24px;
                            margin: 24px 0;
                            border: 1px solid #e2e8f0;
                        }}
                        .credential-item {{
                            padding: 12px 0;
                            border-bottom: 1px solid #f1f5f9;
                        }}
                        .credential-item:last-child {{
                            border-bottom: none;
                        }}
                        .label {{
                            color: #64748b;
                            font-weight: 600;
                            font-size: 0.75rem;
                            text-transform: uppercase;
                            letter-spacing: 0.05em;
                            display: block;
                            margin-bottom: 4px;
                        }}
                        .value {{
                            color: #0f172a;
                            font-weight: 700;
                            font-size: 1.1rem;
                            display: block;
                        }}
                        .footer {{
                            padding: 30px;
                            text-align: center;
                            color: #94a3b8;
                            font-size: 0.8rem;
                            background-color: #f8fafc;
                            border-top: 1px solid #f1f5f9;
                        }}
                        .btn {{
                            display: inline-block;
                            padding: 16px 32px;
                            background: linear-gradient(135deg, #f97316, #ea580c);
                            color: #ffffff !important;
                            text-decoration: none;
                            border-radius: 12px;
                            font-weight: 700;
                            margin-top: 20px;
                            box-shadow: 0 4px 12px rgba(249, 115, 22, 0.3);
                        }}
                    </style>
                </head>
                <body style="background-color: #f8fafc; padding: 40px 20px; margin: 0;">
                    <div class="container">
                        <div class="header">
                            <h1 style="margin: 0; font-size: 28px; font-weight: 800; letter-spacing: -0.02em;">Orange Analytics</h1>
                        </div>
                        <div class="content">
                            <h2 style="margin-top: 0; color: #0f172a; font-size: 20px;">Welcome, {user.username}!</h2>
                            <p style="font-size: 16px; color: #475569;">Your administrative account has been enabled.</p>

                            <div style="background-color: #fff7ed; border-left: 4px solid #f97316; padding: 16px; margin: 24px 0; border-radius: 8px;">
                                <p style="margin: 0; color: #9a3412; font-size: 14px; font-weight: 500;">
                                    <strong>Security Notice:</strong> Your administrative account has been enabled. Please contact your system administrator for more information.
                                </p>
                            </div>
                        </div>
                        <div class="footer">
                            <p style="margin: 0;">&copy; 2026 Orange Analytics &bull; Security & Analysis Suite</p>
                            <p style="margin: 4px 0 0 0;">This is an automated message, please do not reply.</p>
                        </div>
                    </div>
                </body>
                </html>
                """

                msg.attach(MIMEText(html_body, 'html'))

                # Using SMTP to send the email (IMAP is for reading/managing)
                with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                    server.login(sender_email, sender_password)
                    server.send_message(msg)
                    print(f"message sent to {user.email}")
        except Exception as e:
            print(f"Error sending message email: {str(e)}")
        

        

    update_data = user_update.model_dump(exclude_unset=True)
    
    # Handle password update specifically
    if "password" in update_data and update_data["password"]:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin)])
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Delete a user (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    db.delete(user)
    db.commit()
