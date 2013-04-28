from Products.CMFCore.utils import getToolByName


def to44alpha1(context):
    """4.3 -> 4.4alpha1"""
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v44:to44alpha1')
