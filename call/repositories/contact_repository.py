"""
Repository for contact operations.
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from call.models.contact_models import Contact


class ContactRepository:
    """Repository for managing contacts"""

    def add_contact(
        self,
        db: Session,
        user_id: int,
        contact_user_id: int,
        nickname: str
    ) -> Contact:
        """
        Add a new contact for a user.
        
        Args:
            db: Database session
            user_id: User ID adding the contact
            contact_user_id: User ID being added as contact
            nickname: Nickname for the contact
            
        Returns:
            Created Contact object
        """
        contact = Contact(
            user_id=user_id,
            contact_user_id=contact_user_id,
            nickname=nickname
        )
        db.add(contact)
        db.commit()
        db.refresh(contact)
        return contact

    def get_contacts(
        self,
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Contact]:
        """
        Get all contacts for a user.
        
        Args:
            db: Database session
            user_id: User ID
            skip: Pagination offset
            limit: Pagination limit
            
        Returns:
            List of Contact objects
        """
        return db.query(Contact).filter(
            Contact.user_id == user_id
        ).offset(skip).limit(limit).all()

    def get_contact(self, db: Session, contact_id: str) -> Optional[Contact]:
        """
        Get a specific contact by ID.
        
        Args:
            db: Database session
            contact_id: Contact ID
            
        Returns:
            Contact object or None
        """
        return db.query(Contact).filter(Contact.id == contact_id).first()

    def get_contact_by_users(
        self,
        db: Session,
        user_id: int,
        contact_user_id: int
    ) -> Optional[Contact]:
        """
        Get contact if user already has contact_user_id saved.
        
        Args:
            db: Database session
            user_id: User ID
            contact_user_id: Contact user ID
            
        Returns:
            Contact object or None
        """
        return db.query(Contact).filter(
            Contact.user_id == user_id,
            Contact.contact_user_id == contact_user_id
        ).first()

    def delete_contact(self, db: Session, contact_id: str) -> bool:
        """
        Delete a contact.
        
        Args:
            db: Database session
            contact_id: Contact ID
            
        Returns:
            True if deleted, False if not found
        """
        contact = self.get_contact(db, contact_id)
        if not contact:
            return False
        db.delete(contact)
        db.commit()
        return True

    def update_contact_nickname(
        self,
        db: Session,
        contact_id: str,
        new_nickname: str
    ) -> Optional[Contact]:
        """
        Update a contact's nickname.
        
        Args:
            db: Database session
            contact_id: Contact ID
            new_nickname: New nickname
            
        Returns:
            Updated Contact object or None
        """
        contact = self.get_contact(db, contact_id)
        if not contact:
            return None
        contact.nickname = new_nickname
        db.commit()
        db.refresh(contact)
        return contact
