import logging

from Acquisition import aq_parent, aq_base
from plone.keyring.interfaces import IKeyManager
from plone.keyring.keyring import Keyring
from plone.keyring.keymanager import KeyManager
from zope.component import getUtility
from zope.component import getSiteManager
from zope.component.hooks import getSite


logger = logging.getLogger('plone.app.upgrade')


def misc(context):
    logger.info('upgrading keyring')
    manager = getUtility(IKeyManager)

    manager[u'_system'].fill()

    manager[u'_anon'] = Keyring()
    manager[u'_anon'].fill()

    manager[u'_forms'] = Keyring()
    manager[u'_forms'].fill()

    logger.info('add keyring to zope root if not done already')
    app = aq_parent(getSite())
    sm = getSiteManager(app)

    if sm.queryUtility(IKeyManager) is None:
        obj = KeyManager()
        sm.registerUtility(aq_base(obj), IKeyManager, '')
