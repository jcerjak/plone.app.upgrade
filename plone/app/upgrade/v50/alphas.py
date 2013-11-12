import logging
from plone.registry.interfaces import IRegistry
from zope.component import queryUtility
from zope.component import getUtility

from zope.schema.interfaces import IVocabularyFactory

from Products.CMFCore.utils import getToolByName

from plone.app.upgrade.utils import loadMigrationProfile
from plone.app.controlpanel.interfaces import INavigationSchema
from plone.app.controlpanel.interfaces import IEditingSchema

logger = logging.getLogger('plone.app.upgrade')


def to50alpha1(context):
    """4.3 -> 5.0alpha1"""
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v50:to50alpha1')

    # remove obsolete tools
    portal = getToolByName(context, 'portal_url').getPortalObject()
    tools = ['portal_actionicons', 'portal_discussion', 'portal_undo']
    tools = [t for t in tools if t in portal]
    portal.manage_delObjects(tools)


def lowercase_email_login(context):
    """If email is used as login name, lowercase the login names.
    """
    ptool = getToolByName(context, 'portal_properties')
    if ptool.site_properties.getProperty('use_email_as_login'):
        # We want the login name to be lowercase here.  This is new in PAS.
        logger.info("Email is used as login, setting PAS login_transform to "
                    "'lower'.")
        # This can take a while for large sites, as it automatically
        # transforms existing login names to lowercase.  It will fail
        # if this would result in non-unique login names.
        pas = getToolByName(context, 'acl_users')
        pas.manage_changeProperties(login_transform='lower')


def navigation_properties_to_registry(context):
    """"""
    ttool = getToolByName(context , 'portal_types')
    ptool = getToolByName(context, 'portal_properties')
    siteProps = ptool['site_properties']
    navProps = ptool['navtree_properties']

    registry = queryUtility(IRegistry)
    registry.registerInterface(INavigationSchema)
    settings = registry.forInterface(INavigationSchema)
    settings.generate_tabs = not siteProps.disable_folder_sections
    settings.nonfolderish_tabs = not siteProps.disable_nonfolderish_sections

    allTypes = ttool.listContentTypes()
    displayed_types = tuple([
        t for t in allTypes \
        if t not in navProps.metaTypesNotToList])
    settings.displayed_types = displayed_types

    settings.filter_on_workflow = navProps.enable_wf_state_filtering
    settings.workflow_states_to_show = navProps.wf_states_to_show
    settings.show_excluded_items = navProps.showAllParents

def editing_properties_to_registry(context):
    """"""
    ptool = getToolByName(context, 'portal_properties')
    siteProps = ptool['site_properties']
    
    registry = queryUtility(IRegistry)
    registry.registerInterface(IEditingSchema)
    settings = registry.forInterface(IEditingSchema)

    settings.visible_ids = siteProps.visible_ids
    settings.enable_link_integrity_checks = siteProps.enable_link_integrity_checks
    settings.ext_editor = siteProps.ext_editor
    
    factory = getUtility(IVocabularyFactory,'plone.app.vocabularies.AvailableEditors')
    available_editors = factory(context)
    if siteProps.default_editor in available_editors:
        settings.default_editor = siteProps.default_editor
    else:
        #keep the defaul_edior set in the schema
        pass
    settings.lock_on_ttw_edit = siteProps.lock_on_ttw_edit

    
    