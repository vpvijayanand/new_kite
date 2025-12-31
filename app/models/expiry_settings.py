from app import db
from datetime import datetime, date

class ExpirySettings(db.Model):
    __tablename__ = 'expiry_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    underlying = db.Column(db.String(20), nullable=False, unique=True)
    current_expiry = db.Column(db.Date, nullable=False)
    next_expiry = db.Column(db.Date, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ExpirySettings {self.underlying}: {self.current_expiry}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'underlying': self.underlying,
            'current_expiry': self.current_expiry.isoformat() if self.current_expiry else None,
            'next_expiry': self.next_expiry.isoformat() if self.next_expiry else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def get_current_expiry(underlying):
        """Get the current expiry date for an underlying"""
        setting = ExpirySettings.query.filter_by(underlying=underlying.upper()).first()
        if setting:
            return setting.current_expiry
        
        # Fallback to default calculation if not set
        from datetime import timedelta
        today = date.today()
        days_ahead = 3 - today.weekday()  # 3 = Thursday
        if days_ahead <= 0:
            days_ahead += 7
        return today + timedelta(days=days_ahead)
    
    @staticmethod
    def set_expiry_dates(underlying, current_expiry, next_expiry=None):
        """Set or update expiry dates for an underlying"""
        setting = ExpirySettings.query.filter_by(underlying=underlying.upper()).first()
        
        if setting:
            setting.current_expiry = current_expiry
            if next_expiry:
                setting.next_expiry = next_expiry
            setting.updated_at = datetime.utcnow()
        else:
            setting = ExpirySettings(
                underlying=underlying.upper(),
                current_expiry=current_expiry,
                next_expiry=next_expiry,
                updated_at=datetime.utcnow()
            )
            db.session.add(setting)
        
        try:
            db.session.commit()
            return setting
        except Exception as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def get_all_expiry_settings():
        """Get all expiry settings"""
        return ExpirySettings.query.all()
