from Acquisition import aq_inner

from Products.CMFCore.utils import getToolByName

from plone.app.upgrade.tests.base import MigrationTest

import alphas
from plone.registry.interfaces import IRegistry
from zope.component import queryUtility
from zope.component import getUtility
from zope.schema.interfaces import IVocabularyFactory

from plone.app.controlpanel.interfaces import INavigationSchema
from plone.app.controlpanel.interfaces import IEditingSchema
from plone.app.controlpanel.interfaces import IFilterTagsSchema
from plone.app.controlpanel.bbb.filter import XHTML_TAGS
from plone.app.controlpanel.interfaces import ILanguageSchema


class PASUpgradeTest(MigrationTest):

    def afterSetup(self):
        super(PASUpgradeTest, self).afterSetup()
        self.portal_setup = getToolByName(self.portal, 'portal_setup')
        self.portal_setup.runAllImportStepsFromProfile('profile-plone.app.controlpanel:default')

    def test_double_upgrade(self):
        # Check that calling our upgrade twice does no harm.
        alphas.lowercase_email_login(self.portal)
        alphas.lowercase_email_login(self.portal)

    def test_upgrade_with_email_login(self):
        pas = getToolByName(self.portal, 'acl_users')
        regtool = getToolByName(self.portal, 'portal_registration')
        regtool.addMember('JOE', 'somepassword')
        self.assertEqual(pas.getUserById('JOE').getUserName(), 'JOE')

        # First call.
        alphas.lowercase_email_login(self.portal)
        self.assertEqual(pas.getProperty('login_transform'), '')
        self.assertEqual(pas.getUserById('JOE').getUserName(), 'JOE')

        # If email as login is enabled, we want to use lowercase login
        # names, even when that login name is not an email address.
        ptool = getToolByName(self.portal, 'portal_properties')
        ptool.site_properties.manage_changeProperties(use_email_as_login=True)

        # Second call.
        alphas.lowercase_email_login(self.portal)
        self.assertEqual(pas.getProperty('login_transform'), 'lower')
        self.assertEqual(pas.getUserById('JOE').getUserName(), 'joe')

    def test_navigation_properties_to_registry(self):
        registry = queryUtility(IRegistry)
        registry.registerInterface(INavigationSchema)
        ttool = getToolByName(self.portal, 'portal_types')
        ptool = getToolByName(self.portal, 'portal_properties')
        siteProps = ptool['site_properties']
        navProps = ptool['navtree_properties']
        navProps.showAllParents = False
        alphas.navigation_properties_to_registry(self.portal)
        settings = registry.forInterface(INavigationSchema)
        self.assertTrue(not settings.generate_tabs == siteProps.disable_folder_sections)
        self.assertTrue(not settings.nonfolderish_tabs == siteProps.disable_nonfolderish_sections)

        allTypes = ttool.listContentTypes()
        displayed_types = tuple([
            t for t in allTypes
            if t not in navProps.metaTypesNotToList])
        for t in displayed_types:
            self.assertTrue(t in settings.displayed_types)

        self.assertEqual(settings.filter_on_workflow, navProps.enable_wf_state_filtering)
        self.assertEqual(settings.workflow_states_to_show, navProps.wf_states_to_show)
        self.assertEqual(settings.show_excluded_items, navProps.showAllParents)
        self.assertTrue(not settings.show_excluded_items)

    def test_editing_properties_to_registry(self):
        registry = queryUtility(IRegistry)
        registry.registerInterface(IEditingSchema)
        ptool = getToolByName(self.portal, 'portal_properties')
        siteProps = ptool['site_properties']
        alphas.navigation_properties_to_registry(self.portal)
        settings = registry.forInterface(IEditingSchema)

        self.assertEqual(settings.visible_ids, siteProps.visible_ids)
        self.assertEqual(settings.enable_link_integrity_checks, siteProps.enable_link_integrity_checks)
        self.assertEqual(settings.ext_editor, siteProps.ext_editor)
        self.assertEqual(settings.lock_on_ttw_edit, siteProps.lock_on_ttw_edit)

        factory = getUtility(IVocabularyFactory, 'plone.app.vocabularies.AvailableEditors')
        available_editors = factory(self.portal)
        if siteProps.default_editor in available_editors:
            self.assertEqual(settings.default_editor, siteProps.default_editor)
        else:
            self.assertTrue(settings.default_editor in available_editors)

    def test_filter_tag_properties_to_registry(self):
        registry = queryUtility(IRegistry)
        registry.registerInterface(IFilterTagsSchema)
        settings = registry.forInterface(IFilterTagsSchema)
        transform = getattr(
            getToolByName(self.portal, 'portal_transforms'), 'safe_html')
        nasty = transform.get_parameter_value('nasty_tags')
        valid = set(transform.get_parameter_value('valid_tags'))
        stripped = XHTML_TAGS - valid
        custom = valid - XHTML_TAGS
        sorted_nasty = sorted([ctype.decode('utf-8') for ctype in nasty])
        sorted_stripped = sorted([bad.decode('utf-8') for bad in stripped])
        sorted_custom = sorted([cus.decode('utf-8') for cus in custom])
        alphas.filter_tag_properties_to_registry(self.portal)
        self.assertEqual(settings.nasty_tags, sorted_nasty)
        self.assertEqual(settings.stripped_tags, sorted_stripped)
        self.assertEqual(settings.custom_tags, sorted_custom)

    def test_portal_languages_to_registry(self):

        ltool = aq_inner(getToolByName(self.portal,'portal_languages'))
        registry = queryUtility(IRegistry)
        registry.registerInterface(ILanguageSchema)
        settings = registry.forInterface(ILanguageSchema)

        self.assertEqual(settings.use_combined_language_codes, ltool.use_combined_language_codes)
        factory = getUtility(IVocabularyFactory,'plone.app.vocabularies.AvailableContentLanguages')
        available_content_languages = factory(self.portal)
        if ltool.getDefaultLanguage() in available_content_languages:
            self.assertEqual(settings.default_language, ltool.getDefaultLanguage())
        else:
            self.assertTrue(settings.default_language in available_content_languages)
