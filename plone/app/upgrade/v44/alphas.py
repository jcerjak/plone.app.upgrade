from Products.CMFCore.utils import getToolByName


def to44alpha1(context):
    """4.3 -> 4.4alpha1"""
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v43:to43alpha1')
    reindex_sortable_title(context)
    upgradeTinyMCE(context)
    upgradePloneAppTheming(context)
    # XXX only for plone.app.jquery 1.7
    # we're on 1.4 right now
    # upgradePloneAppJQuery(context)


def remove3rdPartyEcmascript(context):
    """plip #12453"""
    qi = getToolByName(context, 'portal_quickinstaller')
    for addon in ('plone.app.sarissa',
                  'plone.app.modernizr',
                  'plone.app.jscalendar'):
        if not qi.isProductInstalled(addon):
            logger.info('install %s' % addon)
            qi.installProduct(addon)
