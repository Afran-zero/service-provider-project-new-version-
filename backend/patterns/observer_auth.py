# patterns/observer_auth.py
# No changes
class Observer:
    def update(self, message, category):
        raise NotImplementedError

class FlashObserver(Observer):
    def update(self, message, category='info'):
        from flask import flash
        flash(message, category)

class Subject:
    def __init__(self):
        self._observers = []

    def attach(self, observer: Observer):
        self._observers.append(observer)

    def notify(self, message, category='info'):
        for obs in self._observers:
            obs.update(message, category)

# Singleton subject to notify anywhere
auth_notifier = Subject()
auth_notifier.attach(FlashObserver())