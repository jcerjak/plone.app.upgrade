import logging
from Acquisition import aq_inner
from plone.registry.interfaces import IRegistry
from zope.component import queryUtility
from zope.component import getUtility

from zope.schema.interfaces import IVocabularyFactory

from Products.CMFCore.utils import getToolByName

from plone.app.upgrade.utils import loadMigrationProfile
from plone.app.controlpanel.interfaces import INavigationSchema
from plone.app.controlpanel.interfaces import IEditingSchema
from plone.app.controlpanel.interfaces import IFilterTagsSchema
from plone.app.controlpanel.bbb.filter import XHTML_TAGS
from plone.app.controlpanel.interfaces import ILanguageSchema

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
    ttool = getToolByName(context, 'portal_types')
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
        t for t in allTypes
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

    factory = getUtility(IVocabularyFactory, 'plone.app.vocabularies.AvailableEditors')
    available_editors = factory(context)
    if siteProps.default_editor in available_editors:
        settings.default_editor = siteProps.default_editor
    else:
        logger.info("The default editor has been changed to %s as the old "
                    "setting %s is no longer available." %
                    (settings.default_editor, siteProps.default_editor))

    settings.lock_on_ttw_edit = siteProps.lock_on_ttw_edit


def filter_tag_properties_to_registry(context):
    """"""
    transform = getattr(
        getToolByName(context, 'portal_transforms'), 'safe_html')

    registry = queryUtility(IRegistry)
    registry.registerInterface(IFilterTagsSchema)
    settings = registry.forInterface(IFilterTagsSchema)

    nasty = transform.get_parameter_value('nasty_tags')
    valid = set(transform.get_parameter_value('valid_tags'))
    stripped = XHTML_TAGS - valid
    custom = valid - XHTML_TAGS
    sorted_nasty = sorted([ctype.decode('utf-8') for ctype in nasty])
    sorted_stripped = sorted([bad.decode('utf-8') for bad in stripped])
    sorted_custom = sorted([cus.decode('utf-8') for cus in custom])
    settings.nasty_tags = sorted_nasty
    settings.stripped_tags = sorted_stripped
    settings.custom_tags = sorted_custom

def portal_languages_to_registry(context):
    """"""
    ltool = aq_inner(getToolByName(context,'portal_languages'))

    registry = queryUtility(IRegistry)
    registry.registerInterface(ILanguageSchema)
    settings = registry.forInterface(ILanguageSchema)

    retrieved_language = ltool.getDefaultLanguage()
    factory = getUtility(IVocabularyFactory, 'plone.app.vocabularies.AvailableContentLanguages')
    available_languages = factory(context)

    if retrieved_language in available_languages:
        settings.default_language = retrieved_language
    else:
        logger.info("The default language was set to %s as the current value "
                    "in portal_languages is no longer available" %
                    (settings.default_language, retrieved_language))
    settings.use_combined_language_codes = ltool.use_combined_language_codes
