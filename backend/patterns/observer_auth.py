# patterns/observer_auth.py
"""
Observer Pattern Implementation for Authentication Notifications

This module implements the Observer pattern for authentication-related events.
Observers are notified when authentication events occur (login, registration, errors, etc.)

Design Pattern: Observer
- Subject: AuthNotificationSubject (manages observers and notifies them)
- Observers: FlashObserver, LoggerObserver, EmailObserver, etc.
- Event: Authentication events with message and category
"""

from abc import ABC, abstractmethod
from typing import List
import logging

logger = logging.getLogger(__name__)


# ============================================
# Observer Interface
# ============================================
class AuthObserver(ABC):
    """Abstract base class for authentication observers"""
    
    @abstractmethod
    def update(self, message: str, category: str = 'info'):
        """Called when an authentication event occurs"""
        pass


# ============================================
# Concrete Observers
# ============================================
class FlashObserver(AuthObserver):
    """Observer that displays flash messages to users"""
    
    def update(self, message: str, category: str = 'info'):
        """Display flash message in the web interface"""
        from flask import flash
        flash(message, category)


class LoggerObserver(AuthObserver):
    """Observer that logs authentication events"""
    
    def __init__(self, log_level: str = 'INFO'):
        self.log_level = log_level
    
    def update(self, message: str, category: str = 'info'):
        """Log authentication events"""
        log_message = f"[AUTH] [{category.upper()}] {message}"
        
        if category == 'danger' or category == 'error':
            logger.error(log_message)
        elif category == 'warning':
            logger.warning(log_message)
        elif category == 'success':
            logger.info(log_message)
        else:
            logger.info(log_message)


class MetricsObserver(AuthObserver):
    """Observer that tracks authentication metrics"""
    
    def __init__(self):
        self.event_counts = {
            'success': 0,
            'danger': 0,
            'warning': 0,
            'info': 0
        }
    
    def update(self, message: str, category: str = 'info'):
        """Track authentication event metrics"""
        self.event_counts[category] = self.event_counts.get(category, 0) + 1
        logger.debug(f"[METRICS] Auth events: {self.event_counts}")
    
    def get_metrics(self):
        """Get current metrics"""
        return self.event_counts.copy()
    
    def reset_metrics(self):
        """Reset metrics counters"""
        self.event_counts = {k: 0 for k in self.event_counts}


# ============================================
# Subject (Observable)
# ============================================
class AuthNotificationSubject:
    """Subject that manages authentication observers and notifies them of events"""
    
    def __init__(self):
        self._observers: List[AuthObserver] = []
        logger.debug("AuthNotificationSubject initialized")
    
    def attach(self, observer: AuthObserver) -> None:
        """Attach an observer to receive notifications"""
        if observer not in self._observers:
            self._observers.append(observer)
            logger.debug(f"Observer {observer.__class__.__name__} attached")
        else:
            logger.warning(f"Observer {observer.__class__.__name__} already attached")
    
    def detach(self, observer: AuthObserver) -> None:
        """Detach an observer from receiving notifications"""
        try:
            self._observers.remove(observer)
            logger.debug(f"Observer {observer.__class__.__name__} detached")
        except ValueError:
            logger.warning(f"Observer {observer.__class__.__name__} not found in observers list")
    
    def notify(self, message: str, category: str = 'info') -> None:
        """Notify all attached observers about an authentication event"""
        logger.debug(f"Notifying {len(self._observers)} observers: [{category}] {message}")
        
        for observer in self._observers:
            try:
                observer.update(message, category)
            except Exception as e:
                logger.error(f"Observer {observer.__class__.__name__} failed: {str(e)}")
    
    def get_observers(self) -> List[AuthObserver]:
        """Get list of attached observers"""
        return self._observers.copy()
    
    def observer_count(self) -> int:
        """Get number of attached observers"""
        return len(self._observers)


# ============================================
# Singleton Instance
# ============================================
auth_notifier = AuthNotificationSubject()

# Attach default observers
auth_notifier.attach(FlashObserver())
auth_notifier.attach(LoggerObserver())

# Attach metrics observer for monitoring
auth_metrics = MetricsObserver()
auth_notifier.attach(auth_metrics)


# ============================================
# Legacy Support (Backward Compatibility)
# ============================================
class Observer(AuthObserver):
    """Legacy base class for backward compatibility"""
    pass


class Subject(AuthNotificationSubject):
    """Legacy subject class for backward compatibility"""
    pass